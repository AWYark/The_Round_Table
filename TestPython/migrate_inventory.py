
import json
import os
import re
from pathlib import Path

from database import inventory_collection

BASE_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = BASE_DIR / "output" / "inventory.json"

# Default to dry-run mode. Import only when explicitly enabled.
IMPORT_ENABLED = os.getenv("MIGRATION_MODE", "dry-run").lower() == "import"

CONDITION_ALIASES = {
    "nm": "Near Mint",
    "near mint": "Near Mint",
    "lp": "Lightly Played",
    "lightly played": "Lightly Played",
    "mp": "Moderately Played",
    "moderately played": "Moderately Played",
    "hp": "Heavily Played",
    "heavily played": "Heavily Played",
    "d": "Damaged",
    "damaged": "Damaged",
}


def normalise_condition(value):
    value = str(value or "Near Mint").strip().casefold()
    return CONDITION_ALIASES.get(value, value.title())


def variant_key(card):
    """Printing identity plus condition and foil status."""
    scryfall_id = card.get("scryfall_id") or card.get("id")

    if scryfall_id:
        printing = ("id", str(scryfall_id))
    else:
        printing = (
            "printing",
            str(card.get("name") or "").strip().casefold(),
            str(card.get("set") or "").strip().lower(),
            str(card.get("collector_number") or "").strip(),
        )

    return printing + (
        normalise_condition(card.get("condition")),
        bool(card.get("foil", False)),
    )


def main():
    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(f"Inventory not found: {INVENTORY_FILE}")

    with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
        source = json.load(file)

    if not isinstance(source, list):
        raise ValueError("inventory.json must contain a list.")

    existing = list(inventory_collection.find({}))
    existing_index = {}

    for record in existing:
        existing_index.setdefault(variant_key(record), []).append(record)

    missing = []
    present = []
    conflicts = []
    seen_source_keys = set()

    for record in source:
        key = variant_key(record)
        name = record.get("name", "Unknown card")

        if key in seen_source_keys:
            conflicts.append(
                (record, f"{name}: duplicate variant in JSON.")
            )
            continue

        seen_source_keys.add(key)
        matches = existing_index.get(key, [])

        if not matches:
            missing.append(record)
        elif len(matches) > 1:
            conflicts.append(
                (record, f"{name}: multiple matching MongoDB records.")
            )
        else:
            mongo_record = matches[0]
            json_quantity = record.get("quantity", 1)
            mongo_quantity = mongo_record.get("quantity", 1)

            if json_quantity != mongo_quantity:
                conflicts.append(
                    (
                        record,
                        f"{name}: JSON quantity={json_quantity}, "
                        f"MongoDB quantity={mongo_quantity}. "
                        "Confirmed choice: keep MongoDB; skip JSON record.",
                    )
                )
            else:
                present.append(record)

    print("========== MIGRATION REPORT ==========")
    print(f"JSON records: {len(source)}")
    print(f"MongoDB records: {len(existing)}")
    print(f"Missing variants: {len(missing)}")
    print(f"Already present with matching quantity: {len(present)}")
    print(f"Conflicts to skip: {len(conflicts)}")

    for record in missing:
        print(
            f"IMPORT CANDIDATE: {record.get('name')} | "
            f"{record.get('set')}/{record.get('collector_number')} | "
            f"{normalise_condition(record.get('condition'))} | "
            f"foil={bool(record.get('foil', False))} | "
            f"qty={record.get('quantity', 1)}"
        )

    for _, message in conflicts:
        print(f"SKIP CONFLICT: {message}")

    if not IMPORT_ENABLED:
        print("\nDRY RUN ONLY: MongoDB was not changed.")
        return

    print("\nImport mode enabled.")

    # Re-check each candidate immediately before inserting.
    # Never overwrite or increase quantities of existing records.
    imported = 0
    skipped = 0

    for record in missing:
        key = variant_key(record)

        query = {
            "condition": normalise_condition(record.get("condition")),
            "foil": bool(record.get("foil", False)),
        }

        scryfall_id = record.get("scryfall_id") or record.get("id")

        printing_match = {
            "name": {
                "$regex": f"^{re.escape(str(record.get('name') or ''))}$",
                "$options": "i",
            },
            "set": str(record.get("set") or "").lower(),
            "collector_number": str(
                record.get("collector_number") or ""
            ),
        }

        identity_conditions = [printing_match]

        if scryfall_id:
            identity_conditions.append({
                "scryfall_id": str(scryfall_id)
            })

        query["$or"] = identity_conditions
        if inventory_collection.find_one(query):
            print(f"SKIP: {record.get('name')} already exists in MongoDB.")
            skipped += 1
            continue

        new_record = dict(record)
        new_record.pop("_id", None)
        new_record["condition"] = normalise_condition(
            new_record.get("condition")
        )
        new_record["foil"] = bool(new_record.get("foil", False))
        new_record["quantity"] = record.get("quantity", 1)

        inventory_collection.insert_one(new_record)
        print(f"IMPORTED: {record.get('name')}")
        imported += 1

    print(f"\nImport complete. Inserted: {imported}; skipped: {skipped}.")
    print("The JSON inventory was not modified.")


if __name__ == "__main__":
    try:
        main()
    finally:
        inventory_collection.database.client.close()
