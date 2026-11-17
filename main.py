
from authentication import (
    ensure_auth_indexes,
    register_user,
    login_user,
)

from view_inventory import run_inventory_manager
from vendor_booth import run_vendor_booth
from scanner2 import run_scanner


def register_menu():
    print("\n========== CREATE ACCOUNT ==========")

    username = input("Username: ").strip()
    email = input("Email: ").strip()
    display_name = input("Display name: ").strip()
    password = input("Password (minimum 12 characters): ")
    confirm_password = input("Confirm password: ")

    if password != confirm_password:
        print("\nPasswords do not match.")
        return

    result = register_user(
        username=username,
        email=email,
        password=password,
        display_name=display_name,
    )

    print(f"\n{result['message']}")

    if result["success"]:
        print(f"Account owner ID: {result['owner_id']}")


def login_menu():
    print("\n========== LOGIN ==========")

    identifier = input("Username or email: ").strip()
    password = input("Password: ")

    result = login_user(identifier, password)

    if not result["success"]:
        print(f"\n{result['message']}")
        return None

    print(f"\nWelcome, {result['user']['display_name']}!")
    return result["user"]


def user_menu(user):
    while True:
        print("\n========== THE ROUND TABLE ==========")
        print(f"Logged in as: {user['display_name']}")
        print(f"Username: {user['username']}")

        print("\n1. View/manage inventory")
        print("2. Open vendor marketplace")
        print("3. Scan a card")
        print("4. Log out")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            run_inventory_manager(user["owner_id"])

        elif choice == "2":
            run_vendor_booth(user["owner_id"])

        elif choice == "3":
            run_scanner(user["owner_id"])

        elif choice == "4":
            print("\nLogged out successfully.")
            break
        else:
            print("Invalid choice. Enter 1, 2, 3, or 4.")


def main():
    print("Initializing The Round Table...")

    ensure_auth_indexes()

    while True:
        print("\n========== THE ROUND TABLE ==========")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            register_menu()

        elif choice == "2":
            user = login_menu()

            if user:
                user_menu(user)

        elif choice == "3":
            print("\nThank you for using The Round Table.")
            break

        else:
            print("Invalid choice. Enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
