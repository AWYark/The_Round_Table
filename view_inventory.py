
import json
from pathlib import Path
import os
from inventory_store import backend
from database import inventory_collection

BASE_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = BASE_DIR / "output" / "inventory.json"


def load_inventory(owner_id):
    if backend == "mongodb":
        return list(
            inventory_collection.find(
                {"owner_id": owner_id}
            )
        )

    if not INVENTORY_FILE.exists():
        return []

    with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_inventory(inventory, owner_id):
    if backend == "mongodb":
        for card in inventory:
            if card.get("_id") is None:
                print(f"Cannot safely update {card.get('name', 'Unknown')}: missing MongoDB ID.")
                continue

            inventory_collection.update_one(
                {
                    "_id": card["_id"],
                    "owner_id": owner_id
                },
                {
                    "$set": {
                        "condition": card.get("condition", "Near Mint"),
                        "foil": card.get("foil", False),
                        "quantity": card.get("quantity", 1),
                    }
                },
            )
        return

    with open(INVENTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(inventory, file, indent=4, ensure_ascii=False)

def get_mongodb_entry_filter(card, owner_id):
    if card.get("_id") is not None:
        return {
            "_id": card["_id"],
            "owner_id": owner_id
        }

    query = {
        "owner_id": owner_id,
        "name": card.get("name"),
        "set": str(card.get("set") or "").lower(),
        "collector_number": str(card.get("collector_number") or ""),
        "condition": card.get("condition", "Near Mint"),
        "foil": bool(card.get("foil", False)),
    }

    if card.get("scryfall_id"):
        query["scryfall_id"] = card["scryfall_id"]

    return query

def find_duplicate_variant(card, original_query, owner_id):
    query = {
        "owner_id": owner_id,
        "name": {
            "$regex": f"^{__import__('re').escape(str(card.get('name') or ''))}$",
            "$options": "i",
        },
        "set": str(card.get("set") or "").lower(),
        "collector_number": str(card.get("collector_number") or ""),
        "condition": card.get("condition", "Near Mint"),
        "foil": bool(card.get("foil", False)),
    }

    if card.get("scryfall_id"):
        query["scryfall_id"] = card["scryfall_id"]

    # Exclude the original document using its unique MongoDB ID.
    original_id = original_query.get("_id")

    if original_id is not None:
        query["_id"] = {"$ne": original_id}

    return inventory_collection.find_one(query)

def display_inventory(cards):
    if not cards:
        print("\nNo cards found.")
        return

    total_copies = 0

    print("\n========== MTG INVENTORY ==========")

    for index, card in enumerate(cards, start=1):
        quantity = card.get("quantity", 1)
        total_copies += quantity

        print(f"\n{index}. {card.get('name', 'Unknown card')}")
        print(f"   Set: {card.get('set_name', 'Unknown set')}")
        print(f"   Set code: {card.get('set', '??').upper()}")
        print(f"   Collector number: {card.get('collector_number', '??')}")
        print(f"   Condition: {card.get('condition', 'Near Mint')}")
        print(f"   Foil: {'Yes' if card.get('foil', False) else 'No'}")
        print(f"   Quantity: {quantity}")

    print("\n===================================")
    print(f"Unique printing entries: {len(cards)}")
    print(f"Total card copies: {total_copies}")


def search_inventory(inventory):
    term = input("Enter a card name to search: ").strip().casefold()

    results = [
        card for card in inventory
        if term in card.get("name", "").casefold()
    ]

    display_inventory(results)



def remove_copy(inventory, owner_id):
    display_inventory(inventory)

    if not inventory:
        return

    try:
        choice = int(input("\nEnter the entry number to reduce: "))

        if not 1 <= choice <= len(inventory):
            print("Invalid entry number.")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    card = inventory[choice - 1]
    quantity = card.get("quantity", 1)

    if backend == "mongodb":
        query = get_mongodb_entry_filter(card, owner_id)
        if quantity > 1:
            result = inventory_collection.update_one(
                query,
                {"$inc": {"quantity": -1}},
            )

            if result.modified_count:
                print(
                    f"Reduced {card['name']} to quantity {quantity - 1}."
                )
            else:
                print("Could not update the selected MongoDB entry.")

        else:
            result = inventory_collection.delete_one(query)

            if result.deleted_count:
                print(f"Removed {card['name']} from MongoDB inventory.")
            else:
                print("Could not find the selected MongoDB entry.")

        return

    if quantity > 1:
        card["quantity"] = quantity - 1
        print(f"Reduced {card['name']} to quantity {card['quantity']}.")
    else:
        inventory.pop(choice - 1)
        print(f"Removed {card['name']} from inventory.")

    save_inventory(inventory, owner_id)


def edit_card_details(inventory, owner_id):
    display_inventory(inventory)

    if not inventory:
        return

    try:
        choice = int(input("\nEnter the entry number to edit: "))

        if not 1 <= choice <= len(inventory):
            print("Invalid entry number.")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    card = inventory[choice - 1]

    # Preserve the original identity before changing condition or foil.
    original_query = get_mongodb_entry_filter(card, owner_id)
    
    print(f"\nEditing: {card.get('name', 'Unknown')}")
    print(f"Current condition: {card.get('condition', 'Near Mint')}")
    print(f"Current foil status: {'Yes' if card.get('foil', False) else 'No'}")

    print("\n--- Choose Card Condition ---")
    print("1. Near Mint")
    print("2. Lightly Played")
    print("3. Moderately Played")
    print("4. Heavily Played")
    print("5. Damaged")

    condition_options = {
        "1": "Near Mint",
        "2": "Lightly Played",
        "3": "Moderately Played",
        "4": "Heavily Played",
        "5": "Damaged",
    }

    condition_choice = input(
        "New condition (1-5, Enter to keep current): "
    ).strip()

    if condition_choice in condition_options:
        card["condition"] = condition_options[condition_choice]
    elif condition_choice:
        print("Invalid condition. Keeping the current condition.")

    foil_choice = input(
        "Is this card foil? (y/n, Enter to keep current): "
    ).strip().lower()

    if foil_choice == "y":
        card["foil"] = True
    elif foil_choice == "n":
        card["foil"] = False
    elif foil_choice not in ("",):
        print("Invalid foil choice. Keeping the current foil status.")


    if backend == "mongodb":
        duplicate = find_duplicate_variant(card, original_query, owner_id)
        
        if duplicate is not None:
            print("\nEdit cancelled: this variant already exists.")
            print("Your MongoDB inventory has not been changed.")
            return

        result = inventory_collection.update_one(
            original_query,
            {
                "$set": {
                    "condition": card.get("condition", "Near Mint"),
                    "foil": card.get("foil", False),
                }
            },
        )

        if result.matched_count:
            print("\nCard details updated successfully in MongoDB.")
            print(f"Condition: {card.get('condition', 'Near Mint')}")
            print(f"Foil: {'Yes' if card.get('foil', False) else 'No'}")
        else:
            print("\nCould not find the original MongoDB entry.")
            print("No MongoDB record was updated.")

        return

    save_inventory(inventory, owner_id)
    
    print("\nCard details updated successfully.")
    print(f"Condition: {card.get('condition', 'Near Mint')}")
    print(f"Foil: {'Yes' if card.get('foil', False) else 'No'}")
    print("Changes saved to inventory.json.")


def update_card_details(card, owner_id, condition, foil, quantity):
    """Update condition and foil status for an owner's MongoDB card."""

    if not owner_id:
        return {
            "success": False,
            "message": "A valid owner ID is required."
        }

    if backend != "mongodb":
        return {
            "success": False,
            "message": "This update currently requires MongoDB."
        }

    valid_conditions = [
        "Near Mint",
        "Lightly Played",
        "Moderately Played",
        "Heavily Played",
        "Damaged",
    ]

    if condition not in valid_conditions:
        return {
            "success": False,
            "message": "Invalid card condition."
        }

    if not isinstance(foil, bool):
        return {
            "success": False,
            "message": "Invalid foil value."
        }

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity < 1
    ):
        return {
            "success": False,
            "message": "Quantity must be a positive whole number."
        }

    # Preserve the original database identity.
    original_query = get_mongodb_entry_filter(card, owner_id)

    # Create a candidate without modifying the loaded card.
    updated_card = dict(card)
    updated_card["condition"] = condition
    updated_card["foil"] = foil

    # Prevent creating a duplicate card variant.
    duplicate = find_duplicate_variant(
        updated_card,
        original_query,
        owner_id
    )

    if duplicate is not None:
        return {
            "success": False,
            "message": "This card variant already exists in your inventory."
        }

    result = inventory_collection.update_one(
        original_query,
        {
            "$set": {
                "condition": condition,
                "foil": foil,
                "quantity": quantity,
            }
        },
    )

    if result.matched_count:
        return {
            "success": True,
            "message": "Card details updated successfully."
        }

    return {
        "success": False,
        "message": "Original inventory entry could not be found."
    }


def remove_inventory_entry(card, owner_id):
    """Remove a complete inventory entry if it has no active listings."""

    if not owner_id:
        return {
            "success": False,
            "message": "A valid owner ID is required."
        }

    if backend != "mongodb":
        return {
            "success": False,
            "message": "Card removal currently requires MongoDB."
        }

    query = get_mongodb_entry_filter(card, owner_id)

    # Confirm the selected inventory entry still exists.
    existing_card = inventory_collection.find_one(query)

    if existing_card is None:
        return {
            "success": False,
            "message": "The selected inventory entry could not be found."
        }

    # Protect cards that are currently listed on the vendor marketplace.
    booth_collection = inventory_collection.database["booth_listings"]

    active_listing = booth_collection.find_one({
        "inventory_id": existing_card["_id"],
        "owner_id": owner_id,
        "status": "active"
    })

    if active_listing:
        return {
            "success": False,
            "message": (
                "This card has an active marketplace listing. "
                "Remove or deactivate that listing first."
            )
        }

    # Delete only this owner's selected inventory entry.
    result = inventory_collection.delete_one(query)

    if result.deleted_count == 1:
        return {
            "success": True,
            "message": (
                f"{existing_card.get('name', 'Card')} "
                "was removed from your inventory."
            )
        }

    return {
        "success": False,
        "message": "The inventory entry could not be removed."
    }

def remove_one_copy(card, owner_id):
    """Remove one copy from an owner's inventory entry."""

    if not owner_id:
        return {
            "success": False,
            "message": "A valid owner ID is required."
        }

    if backend != "mongodb":
        return {
            "success": False,
            "message": "Card removal currently requires MongoDB."
        }

    query = get_mongodb_entry_filter(card, owner_id)

    existing_card = inventory_collection.find_one(query)

    if existing_card is None:
        return {
            "success": False,
            "message": "The selected inventory entry could not be found."
        }

    booth_collection = inventory_collection.database["booth_listings"]

    active_listing = booth_collection.find_one({
        "inventory_id": existing_card["_id"],
        "owner_id": owner_id,
        "status": "active"
    })

    if active_listing:
        return {
            "success": False,
            "message": (
                "This card has an active marketplace listing. "
                "Remove or deactivate that listing first."
            )
        }

    quantity = int(existing_card.get("quantity", 1))

    if quantity <= 1:
        return remove_inventory_entry(card, owner_id)

    result = inventory_collection.update_one(
        {
            **query,
            "quantity": quantity
        },
        {
            "$inc": {
                "quantity": -1
            }
        }
    )

    if result.modified_count == 1:
        return {
            "success": True,
            "message": (
                f"One copy of {existing_card.get('name', 'Card')} "
                "was removed from your inventory."
            )
        }

    return {
        "success": False,
        "message": (
            "The inventory quantity changed or the copy "
            "could not be removed. Please refresh and try again."
        )
    }

def run_inventory_manager(owner_id):
    if not owner_id:
        raise ValueError("A valid owner ID is required.")

    while True:
        inventory = load_inventory(owner_id)

        print("\n========== INVENTORY MENU ==========")
        print("1. View inventory")
        print("2. Search by card name")
        print("3. Remove one copy")
        print("4. Edit card details")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            display_inventory(inventory)
        elif choice == "2":
            search_inventory(inventory)
        elif choice == "3":
            remove_copy(inventory, owner_id)
        elif choice == "4":
            edit_card_details(inventory, owner_id)
        elif choice == "5":
            print("Exiting inventory manager.")
            break
        else:
            print("Invalid choice. Enter 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    DEVELOPMENT_OWNER_ID = "vendor_001"
    run_inventory_manager(DEVELOPMENT_OWNER_ID)