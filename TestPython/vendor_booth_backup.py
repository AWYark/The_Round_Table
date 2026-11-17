import re
import math
from datetime import datetime, timezone

from bson import ObjectId
from database import (
    client,
    inventory_collection,
    marketplace_enquiries_collection,
    db,
)
transactions_collection = db["marketplace_transactions"]
transactions_collection.create_index(
    [("enquiry_id", 1)],
    unique=True,
    name="unique_transaction_per_enquiry",
)

booth_collection = db["booth_listings"]


def get_active_listed_quantity(inventory_id):
    """Return the quantity already committed to active booth listings."""
    result = booth_collection.aggregate([
        {
            "$match": {
                "inventory_id": inventory_id,
                "status": "active"
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$quantity_listed"}
            }
        }
    ])

    totals = list(result)
    return totals[0]["total"] if totals else 0


def get_available_quantity(card):
    """Calculate copies available to list after existing active listings."""
    inventory_id = card["_id"]
    owned_quantity = card.get("quantity", 1)
    already_listed = get_active_listed_quantity(inventory_id)

    return max(0, owned_quantity - already_listed)


def create_listing(
    inventory_id,
    quantity_listed,
    listing_type,
    region,
    price=None,
    currency="NZD",
    trade_options=None
):
    """Create a booth listing for an existing inventory entry."""

    if not isinstance(inventory_id, ObjectId):
        try:
            inventory_id = ObjectId(inventory_id)
        except Exception:
            print("Invalid inventory ID.")
            return False

    card = inventory_collection.find_one({"_id": inventory_id})

    if card is None:
        print("Card was not found in your inventory.")
        return False

    if not isinstance(quantity_listed, int) or isinstance(quantity_listed, bool):
        print("Quantity must be a whole number.")
        return False

    if quantity_listed < 1:
        print("Quantity must be at least 1.")
        return False

    listing_type = listing_type.strip().lower()

    if listing_type not in ("sale", "trade", "sale_and_trade"):
        print("Listing type must be sale, trade, or sale_and_trade.")
        return False

    if not isinstance(region, str) or not region.strip():
        print("Please provide a region.")
        return False

    if listing_type in ("sale", "sale_and_trade"):
        if price is None:
            print("A price is required for sale listings.")
            return False

        try:
            price = float(price)
        except (TypeError, ValueError):
            print("Price must be a valid number.")
            return False

        if price < 0:
            print("Price cannot be negative.")
            return False

    available = get_available_quantity(card)

    if quantity_listed > available:
        print(f"Cannot list {quantity_listed} copies.")
        print(f"Available to list: {available}")
        return False

    now = datetime.now(timezone.utc)

    listing = {
        "inventory_id": inventory_id,
        "owner_id": "vendor_001",
        "card_name": card.get("name", "Unknown card"),
        "set_code": card.get("set", ""),
        "collector_number": card.get("collector_number", ""),
        "condition": card.get("condition", "NM"),
        "foil": card.get("foil", False),
        "quantity_listed": quantity_listed,
        "listing_type": listing_type,
        "price": price if listing_type in ("sale", "sale_and_trade") else None,
        "currency": currency.upper(),
        "trade_options": trade_options or [],
        "region": region.strip(),
        "status": "active",
        "created_at": now,
        "updated_at": now
    }

    result = booth_collection.insert_one(listing)

    print("Vendor booth listing created successfully.")
    print("Listing ID:", result.inserted_id)
    print("Card:", listing["card_name"])
    print("Quantity listed:", quantity_listed)
    print("Region:", listing["region"])

    return True


def view_my_listings():
    """Display all listings stored in the booth collection."""
    listings = list(booth_collection.find().sort("created_at", -1))

    if not listings:
        print("Your vendor booth has no listings yet.")
        return

    print("\n========== MY VENDOR BOOTH ==========")

    for listing in listings:
        print("------------------------------------")
        print("Listing ID:", listing["_id"])
        print("Card:", listing.get("card_name", "Unknown card"))
        print(
            "Printing:",
            listing.get("set_code", ""),
            "/",
            listing.get("collector_number", "")
        )
        print("Condition:", listing.get("condition", "NM"))
        print("Foil:", "Yes" if listing.get("foil", False) else "No")
        print("Quantity:", listing.get("quantity_listed", 0))
        print("Type:", listing.get("listing_type", "sale"))
        print("Price:", listing.get("price"), listing.get("currency", "NZD"))
        print("Region:", listing.get("region", "Not specified"))
        print("Status:", listing.get("status", "unknown"))


def create_listing_menu():
    """Let the user choose an inventory card and create a booth listing."""
    cards = list(inventory_collection.find().sort("name", 1))

    if not cards:
        print("Your inventory is empty.")
        return

    print("\n========== CREATE BOOTH LISTING ==========")

    available_cards = []

    for card in cards:
        available = get_available_quantity(card)

        if available > 0:
            available_cards.append(card)

    if not available_cards:
        print("No inventory copies are currently available to list.")
        return

    for index, card in enumerate(available_cards, start=1):
        print(
            f"{index}. {card.get('name', 'Unknown')} | "
            f"{card.get('set', '')}/{card.get('collector_number', '')} | "
            f"{card.get('condition', 'NM')} | "
            f"Foil: {card.get('foil', False)} | "
            f"Available: {get_available_quantity(card)}"
        )

    try:
        selection = int(input("\nChoose a card number: ").strip())

        if selection < 1 or selection > len(available_cards):
            print("Invalid card selection.")
            return

        card = available_cards[selection - 1]

        quantity = int(input("Quantity to list: ").strip())

        print("\nListing type:")
        print("1. Sale")
        print("2. Trade")
        print("3. Sale and trade")

        type_choice = input("Choose listing type (1-3): ").strip()

        listing_types = {
            "1": "sale",
            "2": "trade",
            "3": "sale_and_trade"
        }

        listing_type = listing_types.get(type_choice)

        if listing_type is None:
            print("Invalid listing type.")
            return

        price = None

        if listing_type in ("sale", "sale_and_trade"):
            price = input("Asking price per copy (NZD): ").strip()

        trade_options = []

        if listing_type in ("trade", "sale_and_trade"):
            trade_text = input(
                "Cards you would accept in trade (comma-separated): "
            ).strip()

            trade_options = [
                item.strip()
                for item in trade_text.split(",")
                if item.strip()
            ]

        region = input(
            "Your region (e.g. Bay of Plenty, New Zealand): "
        ).strip()

        create_listing(
            inventory_id=card["_id"],
            quantity_listed=quantity,
            listing_type=listing_type,
            region=region,
            price=price,
            currency="NZD",
            trade_options=trade_options
        )

    except ValueError:
        print("Please enter a valid number where required.")

def change_listing_status():
    """Activate or deactivate an existing booth listing."""
    listings = list(booth_collection.find().sort("created_at", -1))

    if not listings:
        print("There are no booth listings to manage.")
        return

    print("\n========== MANAGE LISTINGS ==========")

    for index, listing in enumerate(listings, start=1):
        print(
            f"{index}. {listing.get('card_name', 'Unknown')} | "
            f"Quantity: {listing.get('quantity_listed', 0)} | "
            f"Status: {listing.get('status', 'unknown')} | "
            f"ID: {listing['_id']}"
        )

    try:
        selection = int(input("Choose a listing number: ").strip())

        if selection < 1 or selection > len(listings):
            print("Invalid listing selection.")
            return

        listing = listings[selection - 1]
        current_status = listing.get("status", "inactive")

        if current_status == "active":
            new_status = "inactive"
            print("This will release its reserved inventory copies.")
        else:
            new_status = "active"

            card = inventory_collection.find_one({
                "_id": listing["inventory_id"]
            })

            if card is None:
                print("The linked inventory card could not be found.")
                return

            available = get_available_quantity(card)

            # An inactive listing is not included in the active total.
            if listing["quantity_listed"] > available:
                print("Not enough copies are available to reactivate this listing.")
                print("Available to list:", available)
                return

        booth_collection.update_one(
            {"_id": listing["_id"]},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        print(f"Listing status changed to: {new_status}")

    except ValueError:
        print("Please enter a valid listing number.")

def delete_listing():
    """Delete a booth listing without deleting its inventory card."""
    listings = list(booth_collection.find().sort("created_at", -1))

    if not listings:
        print("There are no booth listings to delete.")
        return

    print("\n========== DELETE BOOTH LISTING ==========")

    for index, listing in enumerate(listings, start=1):
        print(
            f"{index}. {listing.get('card_name', 'Unknown')} | "
            f"Quantity: {listing.get('quantity_listed', 0)} | "
            f"Status: {listing.get('status', 'unknown')} | "
            f"ID: {listing['_id']}"
        )

    try:
        selection = int(input("Choose a listing number to delete: ").strip())

        if selection < 1 or selection > len(listings):
            print("Invalid listing selection.")
            return

        listing = listings[selection - 1]

        print("\nYou are about to permanently delete this listing:")
        print("Card:", listing.get("card_name", "Unknown"))
        print("Listing ID:", listing["_id"])
        print("Status:", listing.get("status", "unknown"))

        confirm = input("Delete this listing permanently? (y/n): ").strip().lower()

        if confirm != "y":
            print("Deletion cancelled.")
            return

        print("Deleting listing ID:", repr(listing["_id"]))
        print("Collection:", booth_collection.full_name)

        result = booth_collection.delete_one({"_id": listing["_id"]})
        print("MongoDB deleted count:", result.deleted_count)

        if result.deleted_count == 1:
            print("Listing deleted successfully.")
            print("Your inventory card has not been deleted.")
        else:
            print("Listing was not deleted.")

    except ValueError:
        print("Please enter a valid listing number.")

def browse_marketplace():
    """Browse active booth listings, optionally filtered by region."""
    print("\n========== REGIONAL MARKETPLACE ==========")
    region = input(
        "Enter a region to filter by, or press Enter for all regions: "
    ).strip()

    query = {"status": "active"}

    if region:
        query["region"] = {
            "$regex": f"^{re.escape(region)}$",
            "$options": "i"
        }

    listings = list(
        booth_collection.find(query).sort("created_at", -1)
    )

    if not listings:
        print("No active listings found for that region.")
        return

    print(f"\nActive listings found: {len(listings)}")

    for listing in listings:
        print("------------------------------------")
        print("Card:", listing.get("card_name", "Unknown"))
        print(
            "Printing:",
            listing.get("set_code", ""),
            "/",
            listing.get("collector_number", "")
        )
        print("Condition:", listing.get("condition", "NM"))
        print("Foil:", "Yes" if listing.get("foil", False) else "No")
        print("Quantity:", listing.get("quantity_listed", 0))
        print("Type:", listing.get("listing_type", "sale"))

        if listing.get("price") is not None:
            print(
                "Price per copy:",
                listing["price"],
                listing.get("currency", "NZD")
            )

        if listing.get("trade_options"):
            print("Trade options:", ", ".join(listing["trade_options"]))

        print("Region:", listing.get("region", "Not specified"))

def view_marketplace_listing_details():
    """View the full details of one active marketplace listing."""
    print("\n========== MARKETPLACE LISTING DETAILS ==========")

    listings = list(
        booth_collection.find({"status": "active"}).sort("created_at", -1)
    )

    if not listings:
        print("No active marketplace listings available.")
        return

    for index, listing in enumerate(listings, start=1):
        print(
            f"{index}. {listing.get('card_name', 'Unknown')} "
            f"({listing.get('set_code', '')}/"
            f"{listing.get('collector_number', '')}) - "
            f"{listing.get('region', 'Not specified')}"
        )

    choice = input(
        "Select a listing number, or press Enter to cancel: "
    ).strip()

    if not choice:
        print("Returning to the menu.")
        return

    if not choice.isdigit():
        print("Please enter a valid listing number.")
        return

    index = int(choice)

    if index < 1 or index > len(listings):
        print("Listing number out of range.")
        return

    listing = listings[index - 1]

    print("\n========== LISTING DETAILS ==========")
    print("Listing ID:", listing["_id"])
    print("Card:", listing.get("card_name", "Unknown"))
    print("Set:", listing.get("set_code", "Unknown"))
    print("Collector number:", listing.get("collector_number", "Unknown"))
    print("Condition:", listing.get("condition", "NM"))
    print("Foil:", "Yes" if listing.get("foil", False) else "No")
    print("Quantity listed:", listing.get("quantity_listed", 0))
    print("Listing type:", listing.get("listing_type", "sale"))

    if listing.get("price") is not None:
        print(
            "Price per copy:",
            listing["price"],
            listing.get("currency", "NZD")
        )

    trade_options = listing.get("trade_options", [])
    if trade_options:
        print("Trade options:", ", ".join(trade_options))

    print("Region:", listing.get("region", "Not specified"))
    print("Status:", listing.get("status", "Unknown"))
    print("Created:", listing.get("created_at", "Unknown"))

def submit_marketplace_enquiry():
    """Submit a purchase or trade enquiry for an active listing."""
    print("\n========== SUBMIT MARKETPLACE ENQUIRY ==========")

    listings = list(
        booth_collection.find({"status": "active"}).sort("created_at", -1)
    )

    if not listings:
        print("No active listings are available.")
        return

    for index, listing in enumerate(listings, start=1):
        print(
            f"{index}. {listing.get('card_name', 'Unknown')} "
            f"({listing.get('set_code', '')}/"
            f"{listing.get('collector_number', '')}) - "
            f"{listing.get('region', 'Not specified')}"
        )

    choice = input("Select a listing number, or press Enter to cancel: ").strip()

    if not choice:
        print("Enquiry cancelled.")
        return

    if not choice.isdigit() or not 1 <= int(choice) <= len(listings):
        print("Invalid listing selection.")
        return

    listing = listings[int(choice) - 1]
    listing_type = listing.get("listing_type", "sale")

    allowed_types = []
    if listing_type in ("sale", "sale_and_trade"):
        allowed_types.append("purchase")
    if listing_type in ("trade", "sale_and_trade"):
        allowed_types.append("trade")

    if not allowed_types:
        print("This listing does not accept purchase or trade enquiries.")
        return

    print("\nAvailable enquiry types:")
    if "purchase" in allowed_types:
        print("1. Purchase")
    if "trade" in allowed_types:
        print("2. Trade")

    enquiry_choice = input(
        "Enter the number or name of the enquiry type: "
    ).strip().lower()

    type_options = {}
    if "purchase" in allowed_types:
        type_options["1"] = "purchase"
    if "trade" in allowed_types:
        type_options["2"] = "trade"

    enquiry_type = type_options.get(enquiry_choice, enquiry_choice)

    if enquiry_type not in allowed_types:
        print("That enquiry type is not available for this listing.")
        return
    try:
        quantity = int(input("Quantity requested: ").strip())
    except ValueError:
        print("Please enter a whole number for quantity.")
        return

    available_quantity = listing.get("quantity_listed", 0)
    if quantity < 1 or quantity > available_quantity:
        print(f"Quantity must be between 1 and {available_quantity}.")
        return

    display_name = input("Your display name: ").strip()
    contact = input("Your contact details (email or other agreed contact): ").strip()
    message = input("Message to the listing owner: ").strip()

    if not display_name or not contact:
        print("Display name and contact details are required.")
        return

    if enquiry_type == "trade" and not message:
        print("For a trade enquiry, describe what you are offering in the message.")
        return

    if not listing.get("owner_id"):
        print("This listing has no vendor owner assigned.")
        print("The enquiry cannot be submitted.")
        return
    
    enquiry = {
        "listing_id": listing["_id"],
        "card_name": listing.get("card_name", "Unknown"),
        "listing_owner_id": listing.get("owner_id"),
        "enquiry_type": enquiry_type,
        "quantity_requested": quantity,
        "display_name": display_name,
        "contact": contact,
        "message": message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = marketplace_enquiries_collection.insert_one(enquiry)

    print("\nEnquiry submitted successfully.")
    print("Enquiry ID:", result.inserted_id)
    print("Card:", enquiry["card_name"])
    print("Type:", enquiry_type)
    print("Quantity requested:", quantity)
    print("Status: pending")
    print("Your enquiry has not reserved or removed any cards.")
    
def complete_marketplace_transaction(test_enquiry_id=None):
    """Complete an accepted purchase after payment and handover."""

    print("\n========== COMPLETE PURCHASE ==========")

    enquiry_filter = {
        "listing_owner_id": "vendor_001",
        "enquiry_type": "purchase",
        "status": "accepted",
    }

    if test_enquiry_id is not None:
        enquiry_filter["_id"] = test_enquiry_id
        enquiry_filter["test_label"] = "marketplace_transaction_production_test_v1"
        enquiry_filter["test_record"] = True

    enquiries = list(
        marketplace_enquiries_collection.find(enquiry_filter).sort(
            "created_at", -1
        )
    )    
    
    if not enquiries:
        print("No accepted purchase enquiries are awaiting completion.")
        return

    for index, enquiry in enumerate(enquiries, start=1):
        print(
            f"{index}. {enquiry.get('card_name', 'Unknown')} "
            f"- Quantity: {enquiry.get('quantity_requested', 0)}"
        )

    choice = input(
        "Select a purchase to complete, or press Enter to cancel: "
    ).strip()

    if not choice:
        return

    if not choice.isdigit() or not 1 <= int(choice) <= len(enquiries):
        print("Invalid selection.")
        return

    enquiry = enquiries[int(choice) - 1]

    if input(
        "Confirm payment and handover are complete? (y/n): "
    ).strip().lower() != "y":
        print("Transaction not completed.")
        return

    try:
        with client.start_session() as session:
            with session.start_transaction():
                
                enquiry_query = {
                    "_id": enquiry["_id"],
                    "listing_owner_id": "vendor_001",
                    "status": "accepted",
                    "enquiry_type": "purchase",
                }

                if test_enquiry_id is not None:
                    enquiry_query["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    enquiry_query["test_record"] = True

                current_enquiry = marketplace_enquiries_collection.find_one(
                    enquiry_query,
                    session=session,
                )


                if not current_enquiry:
                    raise ValueError(
                        "The enquiry is no longer eligible for completion."
                    )

                
                listing_query = {
                    "_id": current_enquiry["listing_id"],
                    "owner_id": "vendor_001",
                    "status": "active",
                    "listing_type": {"$in": ["sale", "sale_and_trade"]},
                }

                if test_enquiry_id is not None:
                    listing_query["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    listing_query["test_record"] = True

                listing = booth_collection.find_one(
                    listing_query,
                    session=session,
                )


                if not listing:
                    raise ValueError(
                        "The listing is unavailable or no longer active."
                    )

                quantity = current_enquiry.get("quantity_requested", 0)

                if (
                    not isinstance(quantity, int)
                    or isinstance(quantity, bool)
                    or quantity < 1
                ):
                    raise ValueError("Invalid requested quantity.")

                listed_quantity = listing.get("quantity_listed")

                if (
                    not isinstance(listed_quantity, int)
                    or isinstance(listed_quantity, bool)
                    or listed_quantity < 1
                ):
                    raise ValueError("The listing has an invalid quantity.")

                if quantity > listed_quantity:
                    raise ValueError(
                        "There are not enough listed copies to complete this sale."
                    )

                inventory_id = listing.get("inventory_id")

                
                inventory_query = {"_id": inventory_id}

                if test_enquiry_id is not None:
                    inventory_query["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    inventory_query["test_record"] = True

                inventory = inventory_collection.find_one(
                    inventory_query,
                    session=session,
                )


                if not inventory:
                    raise ValueError("The inventory record was not found.")

                if quantity > inventory.get("quantity", 0):
                    raise ValueError(
                        "There are not enough copies in inventory."
                    )

                now = datetime.now(timezone.utc)
                unit_price = listing.get("price")
                
                if (
                    isinstance(unit_price, bool)
                    or not isinstance(unit_price, (int, float))
                    or not math.isfinite(unit_price)
                    or unit_price < 0
                ):
                    raise ValueError("The listing has an invalid sale price.")
                
                total_price = round(unit_price * quantity, 2)

                
                inventory_update_filter = {
                    "_id": inventory_id,
                    "quantity": {"$gte": quantity},
                }

                if test_enquiry_id is not None:
                    inventory_update_filter["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    inventory_update_filter["test_record"] = True

                inventory_result = inventory_collection.update_one(
                    inventory_update_filter,
                    {
                        "$inc": {"quantity": -quantity},
                        "$set": {"updated_at": now.isoformat()},
                    },
                    session=session,
                )
                
                if inventory_result.modified_count != 1:
                    raise ValueError(
                        "Inventory changed during completion. Please retry."
                    )

                remaining_listed = listed_quantity - quantity

                listing_update = {
                    "quantity_listed": remaining_listed,
                    "updated_at": now,
                }

                if remaining_listed == 0:
                    listing_update["status"] = "completed"

                listing_update_filter = {
                    "_id": listing["_id"],
                    "owner_id": "vendor_001",
                    "status": "active",
                    "quantity_listed": listing["quantity_listed"],
                }

                if test_enquiry_id is not None:
                    listing_update_filter["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    listing_update_filter["test_record"] = True

                listing_result = booth_collection.update_one(
                    listing_update_filter,
                    {"$set": listing_update},
                    session=session,
                )
                
                if listing_result.modified_count != 1:
                    raise ValueError(
                        "Listing changed during completion. Please retry."
                    )

                
                enquiry_update_filter = {
                    "_id": current_enquiry["_id"],
                    "listing_owner_id": "vendor_001",
                    "status": "accepted",
                }

                if test_enquiry_id is not None:
                    enquiry_update_filter["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    enquiry_update_filter["test_record"] = True

                enquiry_result = marketplace_enquiries_collection.update_one(
                    enquiry_update_filter,
                    {
                        "$set": {
                            "status": "completed",
                            "completed_at": now,
                            "updated_at": now,
                        }
                    },
                    session=session,
                )

                if enquiry_result.modified_count != 1:
                    raise ValueError(
                        "Enquiry changed during completion. Please retry."
                    )

                
                transaction_record = {
                    "enquiry_id": current_enquiry["_id"],
                    "listing_id": listing["_id"],
                    "inventory_id": inventory_id,
                    "owner_id": "vendor_001",
                    "buyer_name": current_enquiry.get("display_name", "Unknown"),
                    "transaction_type": "purchase",
                    "card_name": listing.get("card_name", "Unknown"),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "currency": listing.get("currency", "NZD"),
                    "status": "completed",
                    "completed_at": now,
                }

                if test_enquiry_id is not None:
                    transaction_record["test_label"] = (
                        "marketplace_transaction_production_test_v1"
                    )
                    transaction_record["test_record"] = True

                transactions_collection.insert_one(
                    transaction_record,
                    session=session,
                )

        print("Purchase completed successfully.")
        print(f"Card: {listing['card_name']}")
        print(f"Quantity sold: {quantity}")
        print(f"Total: {listing.get('currency', 'NZD')} {total_price:.2f}")

    except ValueError as error:
        print("Purchase not completed:", error)

    except Exception as error:
        print("Purchase failed. Database changes were rolled back.")
        print(type(error).__name__, error)
        
def view_marketplace_enquiries():
    """View and manage purchase and trade enquiries."""
    print("\n========== MARKETPLACE ENQUIRY INBOX ==========")

    enquiries = list(
        marketplace_enquiries_collection.find(
            {
                "listing_owner_id": "vendor_001",
                "status": {"$in": ["pending", "accepted", "declined"]}
            }
        ).sort("created_at", -1)
    )
    
    if not enquiries:
        print("No marketplace enquiries found.")
        return

    for index, enquiry in enumerate(enquiries, start=1):
        print("------------------------------------")
        print(f"{index}. {enquiry.get('card_name', 'Unknown')}")
        print("Enquiry ID:", enquiry["_id"])
        print("Type:", enquiry.get("enquiry_type", "Unknown"))
        print("Quantity requested:", enquiry.get("quantity_requested", 0))
        print("From:", enquiry.get("display_name", "Unknown"))
        print("Contact:", enquiry.get("contact", "Not provided"))
        print("Message:", enquiry.get("message", ""))
        print("Status:", enquiry.get("status", "Unknown"))

    choice = input(
        "\nEnter an enquiry number to manage, or press Enter to return: "
    ).strip()

    if not choice:
        return

    if not choice.isdigit() or not 1 <= int(choice) <= len(enquiries):
        print("Invalid enquiry selection.")
        return

    enquiry = enquiries[int(choice) - 1]

    if enquiry.get("status") != "pending":
        print("Only pending enquiries can be managed.")
        return

    print("\n1. Accept enquiry")
    print("2. Decline enquiry")
    print("3. Cancel")

    action = input("Choose an action: ").strip()

    if action == "3" or not action:
        print("No changes made.")
        return

    if action not in ("1", "2"):
        print("Invalid action.")
        return

    new_status = "accepted" if action == "1" else "declined"

    result = marketplace_enquiries_collection.update_one(
        {
            "_id": enquiry["_id"],
            "listing_owner_id": "vendor_001",
            "status": "pending",
        },
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.modified_count == 1:
        print(f"Enquiry {new_status} successfully.")
        print("No inventory or booth listing quantities were changed.")
    else:
        print("The enquiry was not updated. It may have already changed.")


if __name__ == "__main__":
    while True:
        print("1. View my listings")
        print("2. Create a listing")
        print("3. Manage listing status")
        print("4. Delete a listing")
        print("5. Browse regional marketplace")
        print("6. View marketplace listing details")
        print("7. Submit purchase/trade enquiry")
        print("8. View/manage marketplace enquiries")
        print("9. Complete an accepted purchase")
        print("10. Exit")        
        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_my_listings()
        elif choice == "2":
            create_listing_menu()
        elif choice == "3":
            change_listing_status()
        elif choice == "4":
            delete_listing()
        elif choice == "5":
            browse_marketplace()
        elif choice == "6":
            view_marketplace_listing_details()
        elif choice == "7":
            submit_marketplace_enquiry()
        elif choice == "8":
            view_marketplace_enquiries()
        elif choice == "9":
            complete_marketplace_transaction()
        elif choice == "10":
            break        
        else:
            print("Invalid option. Choose 1 through 10.")