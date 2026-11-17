
from mongo_inventory import add_card_to_inventory
from database import inventory_collection

TEST_ID = "round-table-mongo-inventory-test"

test_card = {
    "id": TEST_ID,
    "name": "Round Table Test Card",
    "set": "tst",
    "set_name": "Test Set",
    "collector_number": "001",
    "rarity": "common",
    "image_uris": {},
    "prices": {
        "usd": "1.00",
        "usd_foil": "2.00",
        "eur": "0.90",
    },
}

try:
    # Clean up any leftovers from an earlier test.
    inventory_collection.delete_many({"scryfall_id": TEST_ID})

    print("\n--- Test 1: Add a new card ---")
    add_card_to_inventory(test_card, "Near Mint", False)

    print("\n--- Test 2: Add the same card again ---")
    add_card_to_inventory(test_card, "Near Mint", False)

    print("\n--- Test 3: Add a different condition ---")
    add_card_to_inventory(test_card, "Lightly Played", False)

    print("\n--- Test 4: Add a foil copy ---")
    add_card_to_inventory(test_card, "Near Mint", True)

    records = list(
        inventory_collection.find({"scryfall_id": TEST_ID})
    )

    print("\n--- Results ---")
    for record in records:
        print(
            f"Condition: {record['condition']}, "
            f"Foil: {record['foil']}, "
            f"Quantity: {record['quantity']}"
        )

    assert len(records) == 3, "Expected 3 separate inventory records."

    quantities = {
        (record["condition"], record["foil"]): record["quantity"]
        for record in records
    }

    assert quantities[("Near Mint", False)] == 2
    assert quantities[("Lightly Played", False)] == 1
    assert quantities[("Near Mint", True)] == 1

    print("\nPASS: All MongoDB inventory tests succeeded!")

except Exception as error:
    print(f"\nTEST FAILED: {error}")
    raise

finally:
    inventory_collection.delete_many({"scryfall_id": TEST_ID})
    print("Test records cleaned up.")
    inventory_collection.database.client.close()
