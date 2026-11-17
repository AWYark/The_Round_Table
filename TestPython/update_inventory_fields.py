import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = BASE_DIR / "output" / "inventory.json"
BACKUP_FILE = BASE_DIR / "output" / "inventory_backup_before_step19.json"


def main():
    if not INVENTORY_FILE.exists():
        print("Inventory file not found.")
        return

    # Read the existing inventory without changing it.
    try:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
            inventory = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read inventory: {error}")
        return

    if not isinstance(inventory, list):
        print("Unexpected inventory format. No changes made.")
        return

    print(f"Found {len(inventory)} inventory entries.")
    confirm = input("Back up and add missing fields? (y/n): ").strip().lower()

    if confirm != "y":
        print("Cancelled. No changes made.")
        return

    # Make a backup before modifying the original.
    try:
        shutil.copy2(INVENTORY_FILE, BACKUP_FILE)
    except OSError as error:
        print(f"Backup failed: {error}")
        print("No changes made.")
        return

    added_condition = 0
    added_foil = 0

    for card in inventory:
        if not isinstance(card, dict):
            print("Unexpected inventory entry. No changes saved.")
            return

        if "condition" not in card:
            card["condition"] = "Near Mint"
            added_condition += 1

        if "foil" not in card:
            card["foil"] = False
            added_foil += 1

    try:
        with open(INVENTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(inventory, file, indent=4, ensure_ascii=False)
    except OSError as error:
        print(f"Could not save updated inventory: {error}")
        print(f"Your original backup is at: {BACKUP_FILE}")
        return

    print("\nStep 19 inventory update complete.")
    print(f"Condition fields added: {added_condition}")
    print(f"Foil fields added: {added_foil}")
    print(f"Backup saved to: {BACKUP_FILE}")
    print(f"Updated inventory: {INVENTORY_FILE}")


if __name__ == "__main__":
    main()
