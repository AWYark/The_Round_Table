from pathlib import Path
from bson import ObjectId

from database import (
    inventory_collection,
    marketplace_enquiries_collection,
    db,
)

booth_collection = db["booth_listings"]
transactions_collection = db["marketplace_transactions"]

ids_file = Path(__file__).with_name("rollback_test_ids.txt")
ids = ids_file.read_text(encoding="utf-8").splitlines()

seller = inventory_collection.find_one({"_id": ObjectId(ids[0])})
buyer = inventory_collection.find_one({"_id": ObjectId(ids[1])})
listing = booth_collection.find_one({"_id": ObjectId(ids[2])})
enquiry = marketplace_enquiries_collection.find_one(
    {"_id": ObjectId(ids[3])}
)

transactions = list(
    transactions_collection.find({"enquiry_id": ObjectId(ids[3])})
)

checks = {
    "Seller quantity unchanged": seller and seller["quantity"] == 2,
    "Buyer quantity unchanged": buyer and buyer["quantity"] == 3,
    "Listing quantity unchanged": listing and listing["quantity_listed"] == 1,
    "Listing remains active": listing and listing["status"] == "active",
    "Enquiry remains accepted": enquiry and enquiry["status"] == "accepted",
    "Only original transaction exists": (
        len(transactions) == 1
        and transactions[0].get("status") == "test_duplicate"
    ),
}

print("\n========== ROLLBACK VERIFICATION ==========")

for description, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {description}")

print("\n========== RESULT ==========")
print(
    "ALL CHECKS PASSED"
    if all(checks.values())
    else "ROLLBACK VERIFICATION FAILED"
)
