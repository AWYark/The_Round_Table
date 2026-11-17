
from bson import ObjectId
from database import db

TEST_LABEL = "marketplace_transaction_test_v1"

inventory_id = ObjectId("6aeaa9b0165fb609da7c3569")
listing_id = ObjectId("6aeaa9b0165fb609da7c356a")
enquiry_id = ObjectId("6aeaa9b0165fb609da7c356b")

inventory = db["inventory"].find_one({
    "_id": inventory_id,
    "test_label": TEST_LABEL,
})

listing = db["booth_listings"].find_one({
    "_id": listing_id,
    "test_label": TEST_LABEL,
})

enquiry = db["marketplace_enquiries"].find_one({
    "_id": enquiry_id,
    "test_label": TEST_LABEL,
})

transactions = list(
    db["marketplace_transactions"].find({
        "test_label": TEST_LABEL,
        "enquiry_id": enquiry_id,
    })
)

print("========== TRANSACTION TEST RESULTS ==========")

print("Inventory quantity:", inventory.get("quantity") if inventory else "MISSING")
print("Listing quantity:", listing.get("quantity_listed") if listing else "MISSING")
print("Listing status:", listing.get("status") if listing else "MISSING")
print("Enquiry status:", enquiry.get("status") if enquiry else "MISSING")
print("Transaction count:", len(transactions))

if transactions:
    transaction = transactions[0]
    print("Transaction status:", transaction.get("status"))
    print("Quantity sold:", transaction.get("quantity"))
    print("Total price:", transaction.get("currency"), transaction.get("total_price"))

print("\n========== VERIFICATION ==========")

passed = (
    inventory is not None
    and inventory.get("quantity") == 1
    and listing is not None
    and listing.get("quantity_listed") == 0
    and listing.get("status") == "completed"
    and enquiry is not None
    and enquiry.get("status") == "completed"
    and len(transactions) == 1
    and transactions[0].get("status") == "completed"
    and transactions[0].get("quantity") == 1
    and transactions[0].get("total_price") == 1.00
)

print("ALL CHECKS PASSED" if passed else "CHECKS FAILED — inspect the results above")
