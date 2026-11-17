
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import PyMongoError

from database import (
    inventory_collection,
    marketplace_enquiries_collection,
    db,
)

booth_collection = db["booth_listings"]
transactions_collection = db["marketplace_transactions"]

TEST_LABEL = "marketplace_transaction_rollback_test_v1"

collections = [
    inventory_collection,
    booth_collection,
    marketplace_enquiries_collection,
    transactions_collection,
]

for collection in collections:
    if collection.count_documents({"test_label": TEST_LABEL}) > 0:
        raise SystemExit(
            f"Rollback test records already exist in {collection.name}. "
            "No new records were created."
        )

now = datetime.now(timezone.utc)
test_name = "TEST CARD - Rollback Workflow"

inventory_id = ObjectId()
buyer_inventory_id = ObjectId()
listing_id = ObjectId()
enquiry_id = ObjectId()
transaction_id = ObjectId()

seller_inventory = {
    "_id": inventory_id,
    "owner_id": "vendor_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "name": test_name,
    "set": "tst",
    "collector_number": "003",
    "condition": "Near Mint",
    "foil": False,
    "quantity": 2,
    "created_at": now.isoformat(),
    "updated_at": now.isoformat(),
}

buyer_inventory = {
    "_id": buyer_inventory_id,
    "owner_id": "buyer_test_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "name": test_name,
    "set": "tst",
    "collector_number": "003",
    "condition": "Near Mint",
    "foil": False,
    "quantity": 3,
    "created_at": now.isoformat(),
    "updated_at": now.isoformat(),
}

listing = {
    "_id": listing_id,
    "inventory_id": inventory_id,
    "owner_id": "vendor_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "card_name": test_name,
    "set_code": "TST",
    "collector_number": "003",
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

enquiry = {
    "_id": enquiry_id,
    "buyer_owner_id": "buyer_test_001",
    "listing_id": listing_id,
    "listing_owner_id": "vendor_001",
    "test_label": TEST_LABEL,
    "test_record": True,
    "enquiry_type": "purchase",
    "card_name": test_name,
    "quantity_requested": 1,
    "display_name": "TEST BUYER",
    "contact_method": "TEST ONLY",
    "message": "Isolated rollback test.",
    "status": "accepted",
    "created_at": now,
    "updated_at": now,
}

# This record deliberately uses the same enquiry_id.
# The transaction insert should therefore fail on the unique index.
existing_transaction = {
    "_id": transaction_id,
    "enquiry_id": enquiry_id,
    "test_label": TEST_LABEL,
    "test_record": True,
    "status": "test_duplicate",
}

inserted = []

try:
    inventory_collection.insert_one(seller_inventory)
    inserted.append((inventory_collection, inventory_id))

    inventory_collection.insert_one(buyer_inventory)
    inserted.append((inventory_collection, buyer_inventory_id))

    booth_collection.insert_one(listing)
    inserted.append((booth_collection, listing_id))

    marketplace_enquiries_collection.insert_one(enquiry)
    inserted.append((marketplace_enquiries_collection, enquiry_id))

    transactions_collection.insert_one(existing_transaction)
    inserted.append((transactions_collection, transaction_id))

except PyMongoError:
    for collection, record_id in reversed(inserted):
        collection.delete_one({"_id": record_id})
    raise

ids_file = "TestPython/rollback_test_ids.txt"

with open(ids_file, "w", encoding="utf-8") as file:
    file.write(f"{inventory_id}\n")
    file.write(f"{buyer_inventory_id}\n")
    file.write(f"{listing_id}\n")
    file.write(f"{enquiry_id}\n")
    file.write(f"{transaction_id}\n")

print("Isolated rollback test records created.")
print("Test label:", TEST_LABEL)
print("Seller starting quantity: 2")
print("Buyer starting quantity: 3")
print("Listing starting quantity: 1")
print("Enquiry status: accepted")
print("Duplicate transaction record: prepared")
print("Rollback test IDs saved.")
