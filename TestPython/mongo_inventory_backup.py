
from datetime import datetime, timezone

from database import inventory_collection


def add_card_to_inventory(card, condition="Near Mint", foil=False):
    """Add a verified card or increase its matching quantity."""

    now = datetime.now(timezone.utc).isoformat()

    set_code = str(card.get("set") or "").lower()
    collector_number = str(card.get("collector_number") or "")
    scryfall_id = card.get("id")

    # Match the exact printing and the requested condition/foil variant.
    card_name = str(card.get("name") or "").strip()

    query = {
        "set": set_code,
        "collector_number": collector_number,
        "name": {
            "$regex": f"^{__import__('re').escape(card_name)}$",
            "$options": "i",
        },
        "condition": condition,
        "foil": foil,
    }

    # Prefer the Scryfall ID when it is available.
    if scryfall_id:
        query = {
            "$and": [
                {"scryfall_id": scryfall_id},
                {
                    "set": set_code,
                    "collector_number": collector_number,
                    "name": {
                        "$regex": f"^{__import__('re').escape(card_name)}$",
                        "$options": "i",
                    },
                },
                {"condition": condition, "foil": foil},
            ]
        }


    # Increase quantity only when printing, condition, and foil match.
    result = inventory_collection.update_one(
        query,
        {
            "$inc": {"quantity": 1},
            "$set": {"updated_at": now},
        },
    )

    if result.matched_count:
        updated = inventory_collection.find_one(query)
        print(f"Quantity increased for {card.get('name')}.")
        print(f"New quantity: {updated['quantity']}")
        return

    # Otherwise, create a separate inventory record.
    record = {
        "scryfall_id": scryfall_id,
        "name": card.get("name"),
        "set": set_code,
        "set_name": card.get("set_name"),
        "collector_number": collector_number,
        "rarity": card.get("rarity"),
        "condition": condition,
        "foil": foil,
        "image_url": (card.get("image_uris") or {}).get("normal"),
        "prices": card.get("prices") or {},
        "quantity": 1,
        "date_added": now,
        "updated_at": now,
    }

    inventory_collection.insert_one(record)

    print(f"Added {record['name']} to MongoDB inventory.")
    print("Quantity: 1")


if __name__ == "__main__":
    print("MongoDB inventory module loaded successfully.")
    print("No inventory records were changed.")
