
from database import inventory_collection
from mongo_inventory import add_card_to_inventory

TEST_NAME = "Round Table Add Test"
TEST_SET = "tst"
TEST_COLLECTOR = "999"

test_filter = {
    "name": TEST_NAME,
    "set": TEST_SET,
    "collector_number": TEST_COLLECTOR,
}

# Remove only previous copies of this synthetic test card.
inventory_collection.delete_many(test_filter)

test_card = {
    "id": "round-table-add-test-scryfall-id",
    "name": TEST_NAME,
    "set": TEST_SET,
    "set_name": "Test Set",
    "collector_number": TEST_COLLECTOR,
    "rarity": "common",
    "image_uris": {"normal": ""},
    "prices": {"usd": "1.00", "usd_foil": "2.00", "eur": "0.90"},
}

# Same variant twice: quantity should become 2.
add_card_to_inventory(test_card, condition="Near Mint", foil=False)
add_card_to_inventory(test_card, condition="Near Mint", foil=False)

# Different condition and foil status: separate entries.
add_card_to_inventory(test_card, condition="Lightly Played", foil=False)
add_card_to_inventory(test_card, condition="Near Mint", foil=True)

records = list(inventory_collection.find(test_filter))

print("\nTest variants:")
for record in records:
    print({
        "condition": record.get("condition"),
        "foil": record.get("foil"),
        "quantity": record.get("quantity"),
    })

print("Number of variants:", len(records))
print("Total quantity:", sum(r.get("quantity", 1) for r in records))
