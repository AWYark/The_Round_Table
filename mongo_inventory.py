
import re
from datetime import datetime, timezone

from database import inventory_collection


def add_card_to_inventory(
    card,
    owner_id,
    condition="Near Mint",
    foil=False,
):
    """Add a verified card to the specified owner's inventory."""

    if not isinstance(owner_id, str) or not owner_id.strip():
        raise ValueError("A valid inventory owner ID is required.")

    owner_id = owner_id.strip()
    now = datetime.now(timezone.utc).isoformat()

    set_code = str(card.get("set") or "").lower()
    collector_number = str(card.get("collector_number") or "")
    scryfall_id = card.get("id")
    card_name = str(card.get("name") or "").strip()

    if not card_name or not set_code or not collector_number:
        raise ValueError("Verified card is missing printing information.")

    query = {
        "owner_id": owner_id,
        "set": set_code,
        "collector_number": collector_number,
        "name": {
            "$regex": f"^{re.escape(card_name)}$",
            "$options": "i",
        },
        "condition": condition,
        "foil": foil,
    }

    if scryfall_id:
        query["scryfall_id"] = scryfall_id

    result = inventory_collection.update_one(
        query,
        {
            "$inc": {"quantity": 1},
            "$set": {"updated_at": now},
        },
    )

    if result.matched_count:
        updated = inventory_collection.find_one(query)
        print(f"Quantity increased for {card_name}.")
        print(f"New quantity: {updated['quantity']}")
        return

    record = {
        "owner_id": owner_id,
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
