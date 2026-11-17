
from database import inventory_collection

TEST_ID = "round_table_inventory_manager_test"

# Remove only a previous test record with this dedicated test ID.
inventory_collection.delete_many({"test_id": TEST_ID})

test_card = {
    "test_id": TEST_ID,
    "scryfall_id": "round-table-test-scryfall-id",
    "name": "Round Table Test Card",
    "set": "tst",
    "set_name": "Test Set",
    "collector_number": "001",
    "rarity": "common",
    "condition": "Near Mint",
    "foil": False,
    "quantity": 2,
    "prices": {},
}

inventory_collection.insert_one(test_card)

print("Temporary test card created.")
print("Initial quantity: 2")
print("Real inventory records were not changed.")
