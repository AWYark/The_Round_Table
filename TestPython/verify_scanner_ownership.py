
from database import inventory_collection, users_collection

print("\n========== SCANNER OWNERSHIP VERIFICATION ==========")

# Find the test member account.
member = users_collection.find_one(
    {"username": "roundtable_test_v1"},
    {"_id": 0, "username": 1, "owner_id": 1}
)

if not member:
    print("ERROR: Test member account not found.")
    raise SystemExit(1)

member_owner_id = member["owner_id"]

print(f"\nTest member owner ID: {member_owner_id}")

# Count records belonging to each account.
member_count = inventory_collection.count_documents(
    {"owner_id": member_owner_id}
)

vendor_count = inventory_collection.count_documents(
    {"owner_id": "vendor_001"}
)

print(f"Test member inventory records: {member_count}")
print(f"Vendor inventory records: {vendor_count}")

# Verify the scanned card.
card = inventory_collection.find_one(
    {
        "owner_id": member_owner_id,
        "name": "Lambholt Harrier",
        "set": "mid",
        "collector_number": "145",
    },
    {"_id": 0}
)

if card:
    print("\nScanned card found:")
    print(f"Name: {card['name']}")
    print(f"Set: {card['set']}")
    print(f"Collector number: {card['collector_number']}")
    print(f"Condition: {card['condition']}")
    print(f"Foil: {card['foil']}")
    print(f"Quantity: {card['quantity']}")
    print(f"Owner ID: {card['owner_id']}")
else:
    print("\nERROR: Scanned card not found under test member.")

# Final checks.
print("\n========== RESULTS ==========")

print("Member card ownership:",
      "PASS" if card else "FAIL")

print("Member inventory count:",
      "PASS" if member_count == 1 else "CHECK")

print("Vendor inventory preserved:",
      "PASS" if vendor_count == 9 else "CHECK")

print("\nVerification complete. No database records were modified.")

