import json
import os
from pathlib import Path
from datetime import datetime, timezone

from database import inventory_collection


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

CARD_FILE = OUTPUT_DIR / "identified_card.json"
INVENTORY_FILE = OUTPUT_DIR / "inventory.json"



def load_inventory():
    """Load inventory from the selected backend."""
    backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

    if backend == "mongodb":
        return list(inventory_collection.find({}))

    if backend != "json":
        raise ValueError("Invalid INVENTORY_BACKEND. Choose 'json' or 'mongodb'.")

    if not INVENTORY_FILE.exists():
        return []

    with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)



def save_inventory(inventory):
    """Save inventory to the selected backend."""
    backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

    if backend == "mongodb":
        raise RuntimeError(
            "Bulk inventory saving is disabled in MongoDB mode. "
            "Use individual MongoDB updates instead."
        )

    if backend != "json":
        raise ValueError("Invalid INVENTORY_BACKEND. Choose 'json' or 'mongodb'.")

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(INVENTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(inventory, file, indent=4, ensure_ascii=False)

def add_card_to_inventory(card, condition="NM", foil=False):
    """Add a card or increase the quantity of an existing printing."""
    inventory = load_inventory()
    backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

    # Use the same condition names as the inventory manager.
    condition_names = {
        "NM": "Near Mint",
        "LP": "Lightly Played",
        "MP": "Moderately Played",
        "HP": "Heavily Played",
        "Damaged": "Damaged",
    }
    condition = condition_names.get(condition, condition)

    set_code = str(card.get("set") or "").lower()
    collector_number = str(card.get("collector_number") or "")
    scryfall_id = card.get("id") or card.get("scryfall_id")
    card_name = card.get("name") or ""

    for entry in inventory:
        same_scryfall_id = (
            scryfall_id
            and entry.get("scryfall_id") == scryfall_id
        )

        same_printing = (
            str(entry.get("set") or "").lower() == set_code
            and str(entry.get("collector_number") or "") == collector_number
            and str(entry.get("name") or "").casefold() == card_name.casefold()
        )

        same_condition = (
            entry.get("condition", "Near Mint") == condition
        )
        same_foil = bool(entry.get("foil", False)) == bool(foil)

        if (same_scryfall_id or same_printing) and same_condition and same_foil:
            new_quantity = entry.get("quantity", 1) + 1
            updated_at = datetime.now(timezone.utc).isoformat()

            if backend == "mongodb":
                if entry.get("_id") is None:
                    raise RuntimeError(
                        f"Cannot safely update {card_name}: missing MongoDB ID."
                    )

                result = inventory_collection.update_one(
                    {"_id": entry["_id"]},
                    {
                        "$set": {
                            "quantity": new_quantity,
                            "updated_at": updated_at,
                        }
                    },
                )

                if result.matched_count == 0:
                    raise RuntimeError(
                        f"Could not find the MongoDB entry for {card_name}."
                    )
            else:
                entry["quantity"] = new_quantity
                entry["updated_at"] = updated_at
                save_inventory(inventory)

            print(f"Quantity increased for {card_name}.")
            print(f"New quantity: {new_quantity}")
            return

    # This printing and variant do not exist yet.
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "scryfall_id": scryfall_id,
        "name": card_name,
        "set": set_code,
        "set_name": card.get("set_name"),
        "collector_number": collector_number,
        "rarity": card.get("rarity"),
        "condition": condition,
        "foil": bool(foil),
        "image_url": (card.get("image_uris") or {}).get("normal")
        or card.get("image_url"),
        "prices": card.get("prices") or {},
        "quantity": 1,
        "date_added": now,
        "updated_at": now,
    }

    if backend == "mongodb":
        inventory_collection.insert_one(record)
    else:
        inventory.append(record)
        save_inventory(inventory)

    print(f"Added {record['name']} to inventory.")
    print("Quantity: 1")

    if backend == "mongodb":
        print("Inventory saved to MongoDB.")
    else:
        print(f"Inventory saved to: {INVENTORY_FILE}")

if __name__ == "__main__":
    if not CARD_FILE.exists():
        print("No verified card found. Run scanner.py first.")
    else:
        with open(CARD_FILE, "r", encoding="utf-8") as file:
            verified_card = json.load(file)

        add_card_to_inventory(verified_card)
