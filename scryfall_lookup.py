
import requests
from urllib.parse import quote


API_URL = "https://api.scryfall.com/cards/named"

HEADERS = {
    "User-Agent": "MTGCardScanner/0.1",
    "Accept": "application/json"
}


def lookup_card(card_name):
    """
    Find an MTG card using a name recognised by OCR.
    Uses Scryfall's fuzzy name matching.
    """

    card_name = card_name.strip()

    if not card_name:
        print("No card name was provided.")
        return None

    params = {
        "fuzzy": card_name
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code == 404:
            print("No matching card was found.")
            return None

        response.raise_for_status()

        card = response.json()

        return card

    except requests.exceptions.Timeout:
        print("Scryfall request timed out.")
    except requests.exceptions.ConnectionError:
        print("Could not connect to Scryfall. Check your internet.")
    except requests.exceptions.HTTPError as error:
        print(f"Scryfall returned an HTTP error: {error}")
    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")

    return None


def lookup_exact_printing(set_code, collector_number):
    """Find a specific MTG printing using its set code and collector number."""

    set_code = set_code.strip().lower()
    collector_number = collector_number.strip()

    if not set_code or not collector_number:
        print("Set code and collector number are both required.")
        return None

    url = f"https://api.scryfall.com/cards/{set_code}/{collector_number}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code == 404:
            print("No card was found for that set code and collector number.")
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        print("Scryfall request timed out.")

    except requests.exceptions.ConnectionError:
        print("Could not connect to Scryfall. Check your internet.")

    except requests.exceptions.HTTPError as error:
        print(f"Scryfall returned an HTTP error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")

    return None



def display_card(card):
    """Display useful card information."""

    if card is None:
        return

    print("\n========== CARD FOUND ==========")
    print(f"Name: {card.get('name', 'Unknown')}")
    print(f"Set: {card.get('set_name', 'Unknown')}")
    print(f"Set code: {card.get('set', 'Unknown')}")
    print(
        f"Collector number: "
        f"{card.get('collector_number', 'Unknown')}"
    )
    print(f"Rarity: {card.get('rarity', 'Unknown')}")
    print(f"Mana cost: {card.get('mana_cost', 'N/A')}")
    print(f"Type: {card.get('type_line', 'Unknown')}")

    print("\nPrices reported by Scryfall:")

    prices = card.get("prices") or {}

    print(f"USD: {prices.get('usd') or 'Unavailable'}")
    print(f"USD foil: {prices.get('usd_foil') or 'Unavailable'}")
    print(f"EUR: {prices.get('eur') or 'Unavailable'}")

    image_uris = card.get("image_uris") or {}
    image_url = image_uris.get("normal")

    # Some double-faced cards store images in card_faces.
    if not image_url:
        faces = card.get("card_faces") or []

        for face in faces:
            face_images = face.get("image_uris") or {}

            if face_images.get("normal"):
                image_url = face_images["normal"]
                break

    print(f"\nCard image: {image_url or 'Unavailable'}")
    print(f"Scryfall page: {card.get('scryfall_uri', 'Unavailable')}")
    print("================================")



if __name__ == "__main__":
    set_code = input("Enter the set code (e.g. lea): ")
    collector_number = input("Enter the collector number (e.g. 161): ")

    card = lookup_exact_printing(set_code, collector_number)

    if card:
        display_card(card)

        import json
        from pathlib import Path

        output_dir = Path(__file__).resolve().parent / "output"
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / "identified_card.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(card, file, indent=4, ensure_ascii=False)

        print(f"\nExact printing saved to: {output_file}")

