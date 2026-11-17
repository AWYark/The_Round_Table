
from getpass import getpass

from authentication import hash_password
from database import users_collection

username = "roundtable_test_v1"

new_password = getpass("Enter a new password (minimum 12 characters): ")

if len(new_password) < 12:
    print("Password must be at least 12 characters.")
    raise SystemExit

confirm_password = getpass("Confirm the new password: ")

if new_password != confirm_password:
    print("Passwords do not match.")
    raise SystemExit

result = users_collection.update_one(
    {"username_normalized": username.casefold()},
    {"$set": {"password_hash": hash_password(new_password)}}
)

if result.matched_count == 1:
    print("Password reset successfully.")
else:
    print("Account not found. No changes made.")
