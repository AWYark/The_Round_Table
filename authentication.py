import re
import bcrypt

from datetime import datetime, timezone
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from database import users_collection

def ensure_auth_indexes():
    """Create unique indexes for new registered accounts."""

    users_collection.create_index(
        "username_normalized",
        unique=True,
        partialFilterExpression={
            "username_normalized": {"$type": "string"}
        },
        name="unique_username_normalized"
    )

    users_collection.create_index(
        "email_normalized",
        unique=True,
        partialFilterExpression={
            "email_normalized": {"$type": "string"}
        },
        name="unique_email_normalized"
    )


def register_user(username, email, password, display_name):
    """Register a new user account."""

    # Validate username.
    username = username.strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,24}", username):
        return {
            "success": False,
            "message": (
                "Username must be 3–24 characters and contain "
                "only letters, numbers or underscores."
            )
        }

    # Normalize username for case-insensitive uniqueness.
    username_normalized = username.casefold()

    # Validate email.
    email = email.strip()
    email_normalized = email.casefold()

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return {
            "success": False,
            "message": "Please enter a valid email address."
        }

    # Validate display name.
    display_name = display_name.strip()

    if not display_name or len(display_name) > 50:
        return {
            "success": False,
            "message": "Display name must be between 1 and 50 characters."
        }

    # Validate and hash password.
    try:
        password_hash = hash_password(password)
    except (ValueError, TypeError) as error:
        return {
            "success": False,
            "message": str(error)
        }

    # Create indexes before inserting.
    ensure_auth_indexes()

    # Generate a new marketplace owner ID.
    owner_id = f"user_{uuid4().hex}"

    user_document = {
        "username": username,
        "username_normalized": username_normalized,
        "email": email,
        "email_normalized": email_normalized,
        "password_hash": password_hash,
        "display_name": display_name,
        "account_type": "member",
        "owner_id": owner_id,
        "created_at": datetime.now(timezone.utc)
    }

    try:
        result = users_collection.insert_one(user_document)

        return {
            "success": True,
            "message": "Account registered successfully.",
            "user_id": str(result.inserted_id),
            "owner_id": owner_id
        }

    except DuplicateKeyError as error:
        key_pattern = error.details.get("keyPattern", {})

        if "username_normalized" in key_pattern:
            message = "That username is already registered."
        elif "email_normalized" in key_pattern:
            message = "That email address is already registered."
        else:
            message = "An account with those details already exists."

        return {
            "success": False,
            "message": message
        }

def login_user(identifier, password):
    """Authenticate a user using their username or email."""

    if not isinstance(identifier, str) or not isinstance(password, str):
        return {
            "success": False,
            "message": "Invalid username/email or password."
        }

    identifier = identifier.strip().casefold()

    if not identifier or not password:
        return {
            "success": False,
            "message": "Invalid username/email or password."
        }

    # Find the account using its normalized username or email.
    user = users_collection.find_one({
        "$or": [
            {"username_normalized": identifier},
            {"email_normalized": identifier}
        ]
    })

    # Verify the password.
    if not user or not verify_password(
        password,
        user.get("password_hash")
    ):
        return {
            "success": False,
            "message": "Invalid username/email or password."
        }

    # Return safe account information only.
    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "user_id": str(user["_id"]),
            "username": user.get("username"),
            "display_name": user.get("display_name"),
            "owner_id": user.get("owner_id"),
            "account_type": user.get("account_type")
        }
    }

def hash_password(password):
    """Securely hash a password using bcrypt."""

    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")

    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 bytes.")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed.decode("utf-8")


def verify_password(password, stored_hash):
    """Verify a password against its stored bcrypt hash."""

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False