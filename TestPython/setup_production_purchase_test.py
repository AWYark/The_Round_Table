
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import PyMongoError

from database import (
    inventory_collection,
    db,
    marketplace_enquiries_collection,
)

booth_collection = db["booth_listings"]

TEST_LABEL = "marketplace_transaction_production_test_v1"

# Refuse to create duplicate test records.
collections = [
    inventory_collection,
    booth_collection,
    marketplace_enquiries_collection,
]

for collection in collections:
    if collection.count_documents({"test_label": TEST_LABEL}) > 0:
        raise SystemExit(
            f"Test records already exist in {collection.name}. "
            "No new records were created."
        )

now = datetime.now(timezone.utc)
test_name = "TEST CARD - Production Workflow"

inventory_id = ObjectId()
listing_id = ObjectId()
enquiry_id = ObjectId()
buyer_inventory_id = ObjectId()

inventory_record = {
    "_id": inventory_id,
    "owner_id": "vendor_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "name": test_name,
    "set": "tst",
    "collector_number": "002",
    "condition": "Near Mint",
    "foil": False,
    "quantity": 2,
    "created_at": now.isoformat(),
    "updated_at": now.isoformat(),
}

listing_record = {
    "_id": listing_id,
    "test_label": TEST_LABEL,
    "test_record": True,
    "inventory_id": inventory_id,
    "owner_id": "vendor_001",
    "card_name": test_name,
    "set_code": "TST",
    "collector_number": "002",
    "condition": "Near Mint",
    "foil": False,
    "quantity_listed": 1,
    "listing_type": "sale",
    "price": 1.00,
    "currency": "NZD",
    "trade_options": [],
    "region": "TEST ONLY",
    "status": "active",
    "created_at": now,
    "updated_at": now,
}

buyer_inventory_record = {
    "_id": buyer_inventory_id,
    "owner_id": "buyer_test_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "name": test_name,
    "set": "tst",
    "collector_number": "002",
    "condition": "Near Mint",
    "foil": False,
    "quantity": 3,
    "created_at": now.isoformat(),
    "updated_at": now.isoformat(),
}

enquiry_record = {
    "_id": enquiry_id,
    "buyer_owner_id": "buyer_test_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "listing_id": listing_id,
    "listing_owner_id": "vendor_001",
    "enquiry_type": "purchase",
    "card_name": test_name,
    "quantity_requested": 1,
    "display_name": "TEST BUYER",
    "contact_method": "TEST ONLY",
    "message": "Isolated production workflow test.",
    "status": "accepted",
    "created_at": now,
    "updated_at": now,
}

inserted = []

try:
    inventory_collection.insert_one(inventory_record)
    inserted.append((inventory_collection, inventory_id))
    
    inventory_collection.insert_one(buyer_inventory_record)
    inserted.append((inventory_collection, buyer_inventory_id))

    booth_collection.insert_one(listing_record)
    inserted.append((booth_collection, listing_id))

    marketplace_enquiries_collection.insert_one(enquiry_record)
    inserted.append((marketplace_enquiries_collection, enquiry_id))

except PyMongoError:
    # Roll back only records created by this script.
    for collection, record_id in reversed(inserted):
        collection.delete_one({"_id": record_id})
    raise

print("Isolated production-test records created.")
print(f"Inventory ID: {inventory_id}")
print(f"Listing ID: {listing_id}")
print(f"Enquiry ID: {enquiry_id}")
print(f"Test label: {TEST_LABEL}")
print("Starting inventory quantity: 2")
print("Starting listing quantity: 1")
print("Starting enquiry status: accepted")
with open(
    "TestPython/production_purchase_test_ids.txt",
    "w",
    encoding="utf-8",
) as file:
    file.write(f"{inventory_id}\n")
    file.write(f"{listing_id}\n")
    file.write(f"{enquiry_id}\n")