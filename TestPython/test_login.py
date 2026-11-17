from authentication import login_user

# Temporary registration test account.
username = "roundtable_test_v1"
email = "roundtable_test_v1@example.com"
password = "RoundTableTest2026!"

print("\n========== LOGIN TEST ==========")

# 1. Correct username and password.
username_login = login_user(username, password)

print("\n--- Username Login ---")
print("Successful:", username_login["success"])
print("Message:", username_login["message"])

# 2. Correct email and password.
email_login = login_user(email, password)

print("\n--- Email Login ---")
print("Successful:", email_login["success"])
print("Message:", email_login["message"])

# 3. Incorrect password.
wrong_password = login_user(username, "WrongPassword2026!")

print("\n--- Incorrect Password ---")
print("Rejected:", not wrong_password["success"])
print("Message:", wrong_password["message"])

# 4. Unknown username.
unknown_user = login_user("unknown_test_user", password)

print("\n--- Unknown Username ---")
print("Rejected:", not unknown_user["success"])
print("Message:", unknown_user["message"])

# 5. Verify returned account information.
if username_login["success"]:
    user = username_login["user"]

    print("\n--- Returned Account Information ---")
    print("Username:", user["username"])
    print("Display name:", user["display_name"])
    print("Owner ID generated:", bool(user["owner_id"]))
    print("Account type:", user["account_type"])
    print("Password hash exposed:", "password_hash" in user)

print("\n========== LOGIN TEST COMPLETE ==========")