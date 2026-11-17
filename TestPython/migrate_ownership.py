from database import db

owner = "vendor_001"

collections = {
    "inventory": "owner_id",
    "booth_listings": "owner_id",
    "marketplace_enquiries": "listing_owner_id"
}

print("========== OWNERSHIP MIGRATION ==========")

for collection_name, owner_field in collections.items():
    collection = db[collection_name]

    result = collection.update_many(
        {},
        {"$set": {owner_field: owner}}
    )

    total = collection.count_documents({})
    owned = collection.count_documents({owner_field: owner})
    incorrect = collection.count_documents({
        owner_field: {"$ne": owner}
    })

    print(f"\n{collection_name}")
    print(f"Matched: {result.matched_count}")
    print(f"Modified: {result.modified_count}")
    print(f"Total records: {total}")
    print(f"Owned by vendor_001: {owned}")
    print(f"Missing or incorrect: {incorrect}")

print("\n========== MIGRATION FINISHED ==========")
