
from database import inventory_collection
from view_inventory import find_duplicate_variant, get_mongodb_entry_filter

TEST_NAME = "Round Table Duplicate Test"
TEST_SET = "tst"
TEST_COLLECTOR = "998"

test_filter = {
    "name": TEST_NAME,
    "set": TEST_SET,
    "collector_number": TEST_COLLECTOR,
}

# Remove leftovers from a previous run of this test only.
inventory_collection.delete_many(test_filter)

test_card = {
    "name": TEST_NAME,
    "set": TEST_SET,
    "collector_number": TEST_COLLECTOR,
    "condition": "Near Mint",
    "foil": False,
    "quantity": 1,
}

# Insert the original temporary record.
inventory_collection.insert_one(test_card.copy())

original = inventory_collection.find_one(test_filter)
original_query = get_mongodb_entry_filter(original)

# Insert a second record with the same variant.
inventory_collection.insert_one(test_card.copy())

# The helper should find the second record, excluding the original.
duplicate = find_duplicate_variant(test_card, original_query)
print("Duplicate detected:", duplicate is not None)

# A different condition should not be considered a duplicate.
different_variant = test_card.copy()
different_variant["condition"] = "Lightly Played"

different_duplicate = find_duplicate_variant(
    different_variant,
    original_query,
)

print("Different condition treated as duplicate:", different_duplicate is not None)

# Remove only this test's temporary records.
cleanup = inventory_collection.delete_many(test_filter)
print("Temporary test records cleaned up:", cleanup.deleted_count)

