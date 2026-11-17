import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from database import inventory_collection


BASE_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = BASE_DIR / "output" / "inventory.json"

# Identify the application when making API requests.
USER_AGENT = "TheRoundTableMTGScanner/1.0"



def load_inventory(owner_id=None):
    backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

    if backend == "mongodb":
        if not owner_id:
            print("Cannot refresh prices without an owner ID.")
            return None

        try:
            return list(
                inventory_collection.find({"owner_id": owner_id})
                )
        except Exception as error:
            print(f"Could not read MongoDB inventory: {error}")
            return None

    if backend != "json":
        print("Invalid INVENTORY_BACKEND. Choose 'json' or 'mongodb'.")
        return None

    if not INVENTORY_FILE.exists():
        print("Inventory file not found.")
        return None

    try:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
            inventory = json.load(file)

        if not isinstance(inventory, list):
            print("Inventory format is invalid; expected a JSON list.")
            return None

        return inventory

    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read inventory: {error}")
        return None

def fetch_scryfall_card(scryfall_id):
    url = f"https://api.scryfall.com/cards/{scryfall_id}"

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def save_inventory(inventory, owner_id=None):
    backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

    if backend == "mongodb":
        if not owner_id:
            raise RuntimeError(
                "Cannot save prices without an owner ID."
            )

        for card in inventory:
            if card.get("_id") is None:
                raise RuntimeError(
                    f"Cannot safely update {card.get('name', 'Unknown')}: "
                    "missing MongoDB ID."
                )

            result = inventory_collection.update_one(
                {
                    "_id": card["_id"],
                    "owner_id": owner_id,
                },
                {
                    "$set": {
                        "prices": card.get("prices") or {},
                        "price_updated_at": card.get("price_updated_at"),
                    }
                },
            )

            if result.matched_count == 0:
                raise RuntimeError(
                    f"MongoDB entry not found or ownership mismatch "
                    f"for {card.get('name', 'Unknown')}."
                )

        return

    if backend != "json":
        raise RuntimeError(
            "Invalid INVENTORY_BACKEND. Choose 'json' or 'mongodb'."
        )

    with open(INVENTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(inventory, file, indent=4, ensure_ascii=False)

def refresh_prices(inventory, owner_id=None):
    updated = 0
    failed = 0
    skipped = 0

    print("\nRefreshing Scryfall prices...")
    print("Your card quantities will not be changed.")

    for index, card in enumerate(inventory, start=1):
        name = card.get("name", "Unknown card")
        scryfall_id = card.get("scryfall_id")

        if not scryfall_id:
            print(f"[SKIP] {name}: missing Scryfall ID.")
            skipped += 1
            continue

        try:
            data = fetch_scryfall_card(scryfall_id)

            # Confirm this is the same Scryfall printing.
            if data.get("id") != scryfall_id:
                print(f"[SKIP] {name}: returned ID did not match.")
                skipped += 1
                continue

            prices = data.get("prices") or {}

            # Keep the same fields used by the valuation summary.
            card["prices"] = {
                "usd": prices.get("usd"),
                "usd_foil": prices.get("usd_foil"),
                "eur": prices.get("eur"),
            }

            card["price_updated_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            updated += 1
            print(
                f"[UPDATED] {name} "
                f"({data.get('set', '').upper()}/"
                f"{data.get('collector_number', '')})"
            )
            print(f"  USD: {prices.get('usd') or 'Unavailable'}")
            print(f"  Foil USD: {prices.get('usd_foil') or 'Unavailable'}")
            print(f"  EUR: {prices.get('eur') or 'Unavailable'}")

        except HTTPError as error:
            print(f"[FAILED] {name}: HTTP {error.code}")
            failed += 1

        except (URLError, TimeoutError, OSError) as error:
            print(f"[FAILED] {name}: network error - {error}")
            failed += 1

        except (json.JSONDecodeError, ValueError) as error:
            print(f"[FAILED] {name}: invalid API response - {error}")
            failed += 1

        # Avoid sending requests too quickly.
        if index < len(inventory):
            time.sleep(0.1)


    # Save only if at least one card was refreshed.
    if updated:
        try:
            save_inventory(inventory, owner_id=owner_id)

            backend = os.getenv(
                "INVENTORY_BACKEND", "json"
            ).strip().lower()

            if backend == "mongodb":
                print("\nUpdated prices saved to MongoDB.")
            else:
                print(f"\nInventory saved to: {INVENTORY_FILE}")

        except Exception as error:
            print(f"\nCould not save updated inventory: {error}")
            return

    print("\n========== REFRESH RESULTS ==========")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print("=====================================")



def main(owner_id=None):
    inventory = load_inventory(owner_id=owner_id)

    if inventory is None:
        return False

    if not inventory:
        print("Your inventory is empty.")
        return True

    print(f"Found {len(inventory)} inventory entries.")

    refresh_prices(inventory, owner_id=owner_id)

    return True


if __name__ == "__main__":
    main()