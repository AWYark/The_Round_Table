from authentication import register_user
from database import users_collection


# Clearly labelled temporary test account.
username = "roundtable_test_v1"
email = "roundtable_test_v1@example.com"
password = "RoundTableTest2026!"
display_name = "Round Table Registration Test"


print("\n========== REGISTRATION TEST ==========")

# 1. Register a new account.
result = register_user(
    username,
    email,
    password,
    display_name
)

print("\n--- New Registration ---")
print("Success:", result["success"])
print("Message:", result["message"])

if not result["success"]:
    print("Registration test stopped.")
    raise SystemExit(1)

# 2. Verify the account was saved.
user = users_collection.find_one(
    {"owner_id": result["owner_id"]}
)

print("\n--- Database Verification ---")
print("User saved:", user is not None)
print("Username saved:", user.get("username") == username)
print("Email saved:", user.get("email") == email)
print("Password hash saved:", bool(user.get("password_hash")))
print("Plaintext password stored:", password == user.get("password_hash"))
print("Account type:", user.get("account_type"))
print("Owner ID generated:", bool(user.get("owner_id")))

# 3. Test duplicate username.
duplicate_username = register_user(
    "ROUNDTABLE_TEST_V1",
    "another_test@example.com",
    "AnotherTestPassword2026!",
    "Duplicate Username Test"
)

print("\n--- Duplicate Username Test ---")
print("Rejected:", not duplicate_username["success"])
print("Message:", duplicate_username["message"])

# 4. Test duplicate email.
duplicate_email = register_user(
    "another_test_user",
    "ROUNDTABLE_TEST_V1@EXAMPLE.COM",
    "AnotherTestPassword2026!",
    "Duplicate Email Test"
)

print("\n--- Duplicate Email Test ---")
print("Rejected:", not duplicate_email["success"])
print("Message:", duplicate_email["message"])

print("\n========== REGISTRATION TEST COMPLETE ==========")
