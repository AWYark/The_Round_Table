
import re
from getpass import getpass

from pymongo.errors import DuplicateKeyError

from authentication import hash_password, ensure_auth_indexes
from database import users_collection


OWNER_ID = "vendor_001"


def main():
    print("========== LINK EXISTING VENDOR ACCOUNT ==========")

    username = input("Choose a username: ").strip()
    email = input("Enter email address: ").strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,24}", username):
        print("Username must be 3-24 characters.")
        return

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        print("Please enter a valid email address.")
        return

    password = getpass("Choose a password (minimum 12 characters): ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    try:
        password_hash = hash_password(password)
    except (ValueError, TypeError) as error:
        print(f"Password validation failed: {error}")
        return

    ensure_auth_indexes()

    try:
        result = users_collection.update_one(
            {"owner_id": OWNER_ID},
            {
                "$set": {
                    "username": username,
                    "username_normalized": username.casefold(),
                    "email": email,
                    "email_normalized": email.casefold(),
                    "password_hash": password_hash,
                }
            }
        )

        if result.matched_count:
            print("\nVendor login credentials linked successfully.")
            print("Existing owner ID preserved:", OWNER_ID)
        else:
            print("\nExisting vendor account was not found.")

    except DuplicateKeyError:
        print("\nThat username or email is already registered.")


if __name__ == "__main__":
    main()

