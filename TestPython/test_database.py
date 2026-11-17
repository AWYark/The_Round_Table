
from database import inventory_collection

test_id = "round_table_connection_test"

test_card = {
    "test_id": test_id,
    "name": "Database Connection Test",
    "set_code": "TEST",
    "collector_number": "001",
    "condition": "Near Mint",
    "foil": False,
    "quantity": 1
}

try:
    # Remove an earlier test document, if one exists.
    inventory_collection.delete_one({"test_id": test_id})

    # Insert the test document.
    result = inventory_collection.insert_one(test_card)
    print("Test document inserted:", result.inserted_id)

    # Retrieve the document.
    saved_card = inventory_collection.find_one({"test_id": test_id})

    if saved_card:
        print("Test document retrieved successfully!")
        print("Card name:", saved_card["name"])
        print("Quantity:", saved_card["quantity"])
    else:
        print("ERROR: Test document could not be retrieved.")

    # Delete only our test document.
    cleanup = inventory_collection.delete_one({"test_id": test_id})

    if cleanup.deleted_count == 1:
        print("Test document deleted successfully.")
    else:
        print("WARNING: Test document was not deleted.")

except Exception as error:
    print("Database test failed:", error)

finally:
    inventory_collection.database.client.close()
