
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess
import sys

from database import inventory_collection


BASE_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = BASE_DIR / "output" / "inventory.json"

def load_inventory():
    backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

    if backend == "mongodb":
        try:
            return list(inventory_collection.find({}))
        except Exception as error:
            print(f"Could not read MongoDB inventory: {error}")
            return []

    if backend != "json":
        print("Invalid INVENTORY_BACKEND. Choose 'json' or 'mongodb'.")
        return []

    if not INVENTORY_FILE.exists():
        print("Inventory not found. Scan a card first.")
        return []

    try:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read inventory: {error}")
        return []

def show_card_summary(card, index):
    quantity = card.get("quantity", 1)
    prices = card.get("prices") or {}

    condition = card.get("condition", "Near Mint")
    foil = card.get("foil", False)

    multiplier = CONDITION_MULTIPLIERS.get(condition, 1.00)

    print("\n" + "=" * 45)
    print(f"CARD SUMMARY #{index}")
    print("=" * 45)

    print(f"Name: {card.get('name', 'Unknown')}")
    print(f"Set: {card.get('set_name', 'Unknown')}")
    print(f"Set code: {card.get('set', '??').upper()}")
    print(f"Collector number: {card.get('collector_number', '??')}")
    print(f"Rarity: {card.get('rarity', 'Unknown').title()}")
    print(f"Quantity owned: {quantity}")
    print(f"Condition: {condition}")
    print(f"Foil: {'Yes' if foil else 'No'}")

    print("\n--- Scryfall Price Reference ---")
    print(f"USD (nonfoil): {format_price(prices.get('usd'), 'USD')}")
    print(f"USD (foil): {format_price(prices.get('usd_foil'), 'USD')}")
    print(f"EUR (nonfoil): {format_price(prices.get('eur'), 'EUR')}")

    # Select the appropriate market price.
    if foil:
        price = prices.get("usd_foil")
    else:
        price = prices.get("usd")

    # Fall back to nonfoil pricing if the selected price is unavailable.
    if price is None or price == "":
        price = prices.get("usd")

    print("\n--- Estimated Resale Value ---")

    if price is not None and price != "":
        try:
            base_price = float(price)
            adjusted_price = base_price * multiplier
            total_usd = adjusted_price * quantity
            total_nzd = total_usd * NZD_PER_USD

            print(f"Market price per card: USD {base_price:.2f}")
            print(f"Condition adjustment: {multiplier:.0%}")
            print(f"Estimated value per card: USD {adjusted_price:.2f}")
            print(f"Estimated collection value: USD {total_usd:.2f}")
            print(f"Estimated collection value: NZD {total_nzd:.2f}")

        except (ValueError, TypeError):
            print("Estimated resale value: Unavailable")
    else:
        print("Estimated resale value: Unavailable")

    print(f"\nScryfall image: {card.get('image_url') or 'Unavailable'}")
    print("=" * 45)


def format_price(value, currency):
    if value is None or value == "":
        return "Unavailable"

    try:
        return f"{currency} {float(value):.2f}"
    except (ValueError, TypeError):
        return "Unavailable"


# Approximate exchange rate: update this when needed.
NZD_PER_USD = 1.75

CONDITION_MULTIPLIERS = {
    "Near Mint": 1.00,
    "Lightly Played": 0.85,
    "Moderately Played": 0.70,
    "Heavily Played": 0.50,
    "Damaged": 0.30,
}


def show_collection_valuation(inventory):
    total_copies = 0
    priced_copies = 0
    missing_price_copies = 0
    total_value_usd = 0.0

    for card in inventory:
        quantity = card.get("quantity", 1)
        prices = card.get("prices") or {}

        # Select the market price based on foil status.
        if card.get("foil", False):
            price = prices.get("usd_foil")
        else:
            price = prices.get("usd")

        # Fall back to the nonfoil price if foil pricing is unavailable.
        if price is None or price == "":
            price = prices.get("usd")

        total_copies += quantity

        if price is None or price == "":
            missing_price_copies += quantity
            continue

        try:
            base_price = float(price)
            condition = card.get("condition", "Near Mint")
            multiplier = CONDITION_MULTIPLIERS.get(condition, 1.00)

            adjusted_price = base_price * multiplier
            total_value_usd += adjusted_price * quantity
            priced_copies += quantity

        except (ValueError, TypeError):
            missing_price_copies += quantity

    total_value_nzd = total_value_usd * NZD_PER_USD

    print("\n" + "=" * 45)
    print("THE ROUND TABLE - COLLECTION VALUATION")
    print("=" * 45)
    print(f"Unique printing entries: {len(inventory)}")
    print(f"Total card copies: {total_copies}")
    print(f"Copies with usable prices: {priced_copies}")
    print(f"Copies without usable prices: {missing_price_copies}")
    print("-" * 45)
    print(f"Estimated resale value: USD {total_value_usd:.2f}")
    print(f"Estimated resale value: NZD {total_value_nzd:.2f}")
    print("=" * 45)


def run_price_refresh():
    refresh_script = BASE_DIR / "refresh_price.py"

    if not refresh_script.exists():
        print("Could not find refresh_price.py.")
        return

    subprocess.run(
        [sys.executable, str(refresh_script)],
        check=False
    )


def main():
    inventory = load_inventory()

    if not inventory:
        print("Your inventory is empty.")
        return

    print("\nTHE ROUND TABLE - CARD VALUATION SUMMARY")
    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Unique printing entries: {len(inventory)}")

    total_copies = sum(card.get("quantity", 1) for card in inventory)
    print(f"Total card copies: {total_copies}")

    while True:
        print("\nChoose an option:")
        print("1. View all card summaries")
        print("2. Search for a card")
        print("3. View collection valuation")
        print("4. Refresh prices from Scryfall")
        print("5. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            for index, card in enumerate(inventory, start=1):
                show_card_summary(card, index)

        elif choice == "2":
            term = input("Enter card name: ").strip().casefold()

            matches = [
                card for card in inventory
                if term and term in card.get("name", "").casefold()
            ]

            if matches:
                for index, card in enumerate(matches, start=1):
                    show_card_summary(card, index)
            else:
                print("No matching cards found.")

        elif choice == "3":
            show_collection_valuation(inventory)
            
        elif choice == "4":
            run_price_refresh()
    
        elif choice == "5":
            print("Exiting card summary.")
            break
        
        else:
            print("Invalid choice. Enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()
