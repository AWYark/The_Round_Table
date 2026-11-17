
from pathlib import Path

from database import (
    inventory_collection,
    marketplace_enquiries_collection,
    db,
)

booth_collection = db["booth_listings"]
transactions_collection = db["marketplace_transactions"]

TEST_LABEL = "marketplace_transaction_production_test_v1"

ids_file = Path(__file__).with_name("production_purchase_test_ids.txt")

if not ids_file.exists():
    raise SystemExit("Test IDs not found.")

ids = ids_file.read_text(encoding="utf-8").splitlines()

if len(ids) != 3:
    raise SystemExit("Test ID file is incomplete.")

from bson import ObjectId

inventory_id = ObjectId(ids[0])
listing_id = ObjectId(ids[1])
enquiry_id = ObjectId(ids[2])

inventory = inventory_collection.find_one({"_id": inventory_id})
listing = booth_collection.find_one({"_id": listing_id})
enquiry = marketplace_enquiries_collection.find_one({"_id": enquiry_id})
transaction = transactions_collection.find_one({"enquiry_id": enquiry_id})

buyer_owner_id = enquiry.get("buyer_owner_id") if enquiry else None

buyer_inventory = None

if buyer_owner_id:
    buyer_inventory = inventory_collection.find_one({
        "owner_id": buyer_owner_id,
        "name": "TEST CARD - Production Workflow",
        "set": "tst",
        "collector_number": "002",
        "condition": "Near Mint",
        "foil": False,
        "test_label": TEST_LABEL,
        "test_record": True,
    })

print("\n========== PRODUCTION TEST VERIFICATION ==========")

print("\n--- Seller Inventory ---")
print("Quantity:", inventory.get("quantity") if inventory else "MISSING")

print("\n--- Buyer Inventory ---")
print("Buyer owner ID:", buyer_owner_id)
print("Quantity received:", buyer_inventory.get("quantity") if buyer_inventory else "MISSING")

print("\n--- Listing ---")
print("Quantity listed:", listing.get("quantity_listed") if listing else "MISSING")
print("Status:", listing.get("status") if listing else "MISSING")

print("\n--- Enquiry ---")
print("Status:", enquiry.get("status") if enquiry else "MISSING")

print("\n--- Transaction ---")
if transaction:
    print("Status:", transaction.get("status"))
    print("Buyer owner ID:", transaction.get("buyer_owner_id"))
    print("Quantity sold:", transaction.get("quantity"))
    print("Total price:", transaction.get("total_price"))
else:
    print("MISSING")

checks = [
    inventory is not None
    and inventory.get("test_label") == TEST_LABEL
    and inventory.get("quantity") == 1,

    buyer_inventory is not None
    and buyer_inventory.get("quantity") == 4,

    listing is not None
    and listing.get("test_label") == TEST_LABEL
    and listing.get("quantity_listed") == 0
    and listing.get("status") == "completed",

    enquiry is not None
    and enquiry.get("test_label") == TEST_LABEL
    and enquiry.get("status") == "completed",

    transaction is not None
    and transaction.get("test_label") == TEST_LABEL
    and transaction.get("test_record") is True
    and transaction.get("status") == "completed"
    and transaction.get("quantity") == 1
    and transaction.get("total_price") == 1.0
    and transaction.get("buyer_owner_id") == buyer_owner_id,
]

print("\n========== RESULT ==========")

if all(checks):
    print("ALL CHECKS PASSED")
    print("Seller deduction verified.")
    print("Buyer inventory credit verified.")
    print("Transaction history verified.")
else:
    print("SOME CHECKS FAILED")
    print("Review the results above before proceeding.")

