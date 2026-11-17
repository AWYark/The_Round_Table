
import os

from dotenv import load_dotenv
from pymongo import MongoClient

# Load credentials from the project's .env file.
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI is missing. Check your .env file."
    )

# Create the database connection.
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000
)

# Select the database (created automatically when data is inserted).
db = client["the_round_table"]

# Collection for card inventory records.
inventory_collection = db["inventory"]
# Collection for marketplace purchase and trade enquiries.
marketplace_enquiries_collection = db["marketplace_enquiries"]
# Collection for user registration and login.
users_collection = db["users"]

def test_connection():
    """Check whether MongoDB Atlas is reachable."""
    try:
        client.admin.command("ping")
        print("MongoDB Atlas connection successful!")
        print("Database: the_round_table")
        print("Collection: inventory")
        return True

    except Exception as error:
        print("MongoDB Atlas connection failed.")
        print(f"Error: {error}")
        return False


if __name__ == "__main__":
    test_connection()
    client.close()
