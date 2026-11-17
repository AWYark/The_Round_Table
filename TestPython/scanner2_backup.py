
import cv2
import numpy as np
import pytesseract
from pathlib import Path
import re
import os
from scryfall_lookup import lookup_card,lookup_exact_printing ,display_card
from inventory_store import add_card_to_inventory

OWNER_ID = os.getenv("ROUND_TABLE_OWNER_ID")

# ==========================================
# CONFIGURATION
# ==========================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CARD_CROP = OUTPUT_DIR / "06_card_crop.jpg"
#ORIGINAL_IMAGE = BASE_DIR / "images" / "Xyris-the-Writhing-Storm.jpg"
ORIGINAL_IMAGE = None




def extract_printing_details(image):
    """Extract collector number and set code from the card's bottom edge."""

    height, width = image.shape[:2]

    # Crop the lower-left text area.
    x1 = int(width * 0.04)
    x2 = int(width * 0.52)
    y1 = int(height * 0.935)
    y2 = int(height * 0.985)

    crop = image[y1:y2, x1:x2]

    if crop.size == 0:
        print("Could not crop the collector information.")
        return None, None

    # Enlarge the crop to improve recognition of small text.
    enlarged = cv2.resize(
        crop,
        None,
        fx=4,
        fy=4.5,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

    # Improve local contrast.
    gray = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    ).apply(gray)

    # Add a white border to separate text from the image edge.
    gray = cv2.copyMakeBorder(
        gray,
        15, 15, 15, 15,
        cv2.BORDER_CONSTANT,
        value=255
    )

    # Create two OCR preprocessing options.
    _, thresholded = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    cv2.imwrite(
        str(OUTPUT_DIR / "11_bottom_crop.jpg"),
        crop
    )
    cv2.imwrite(
        str(OUTPUT_DIR / "12_bottom_ocr.jpg"),
        thresholded
    )

    # Try both grayscale and thresholded images.
    ocr_results = []

    for method_name, processed in [
        ("grayscale", gray),
        ("otsu", thresholded)
    ]:
        for page_mode in (6, 7, 11):
            text = pytesseract.image_to_string(
                processed,
                config=f"--oem 3 --psm {page_mode}"
            )

            if text.strip():
                ocr_results.append(
                    (method_name, page_mode, text.strip())
                )

    print("\n========== BOTTOM OCR CANDIDATES ==========")

    for method_name, page_mode, text in ocr_results:
        print(
            f"{method_name} | PSM {page_mode} | "
            f"{text.replace(chr(10), ' / ')}"
        )

    # Combine candidate text so a separator recognised in one
    # version is not lost if another version misses it.
    combined_text = "\n".join(
        text for _, _, text in ocr_results
    ).upper()

    filtered_text = re.sub(
        r"[^A-Z0-9\s/•*★>:_-]",
        "",
        combined_text
    )

    clean_text = re.sub(
        r"[^A-Z0-9]",
        "",
        filtered_text
    )

    print(f"\nFiltered bottom OCR:\n{filtered_text}")
    print(f"Cleaned bottom OCR: {clean_text}")

    # Extract a collector number such as 303/322 or 018.
    number_match = re.search(
        r"\b(\d{1,4}[A-Z]?)\s*(?:/\s*\d{1,4})?\b",
        filtered_text
    )

    # Find a set code before the English language marker.
    # Permit punctuation and separators between the fields.
    set_match = re.search(
        r"\b([A-Z0-9]{2,6})\b"
        r"[\s*•>:/_-]*"
        r"\bEN\b",
        filtered_text
    )

    collector_number = (
        number_match.group(1) if number_match else None
    )
    set_code = set_match.group(1) if set_match else None

    print("\n========== BOTTOM OCR RESULT ==========")
    print(f"Extracted collector number: {collector_number}")
    print(f"Extracted set code: {set_code}")

    return set_code, collector_number

# ==========================================
# LOAD CARD IMAGE
# ==========================================


# Select an image to scan.
image_files = (
    list((BASE_DIR / "images").glob("*.jpg"))
    + list((BASE_DIR / "images").glob("*.jpeg"))
    + list((BASE_DIR / "images").glob("*.png"))
)

if not image_files:
    print("No card images found in the images folder.")
    raise SystemExit(1)

print("\n========== AVAILABLE CARD IMAGES ==========")

for index, image_path in enumerate(image_files, start=1):
    print(f"{index}. {image_path.name}")

while True:
    choice = input("\nEnter the image number to scan: ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(image_files):
        selected_image = image_files[int(choice) - 1]
        break

    print("Invalid selection. Enter one of the listed numbers.")

print(f"\nSelected image: {selected_image.name}")

# Load the selected image.
image = cv2.imread(str(selected_image))

if image is None:
    print("Could not load the selected image.")
    raise SystemExit(1)

print(f"Image loaded successfully: {image.shape[1]} x {image.shape[0]}")


# ==========================================
# CROP CARD NAME REGION
# ==========================================

height, width = image.shape[:2]

# Approximate title bar of a standard MTG card.
# Adjust these percentages if your title is outside
# the saved crop.

top = int(height * 0.044)
bottom = int(height * 0.1)
left = int(width * 0.069)
right = int(width * 0.93)

name_crop = image[top:bottom, left:right]

if name_crop.size == 0:
    raise ValueError("The title crop is empty.")

cv2.imwrite(
    str(OUTPUT_DIR / "09_name_original.jpg"),
    name_crop
)


# ==========================================
# PREPROCESS IMAGE
# ==========================================

gray = cv2.cvtColor(
    name_crop,
    cv2.COLOR_BGR2GRAY
)

# Enlarge the title for OCR.
gray = cv2.resize(
    gray,
    None,
    fx=4,
    fy=4,
    interpolation=cv2.INTER_CUBIC
)

# Reduce small image noise.
gray = cv2.GaussianBlur(
    gray,
    (3, 3),
    0
)

# Add a white border to help Tesseract
# recognise text near the crop edges.
gray = cv2.copyMakeBorder(
    gray,
    20, 20, 20, 20,
    cv2.BORDER_CONSTANT,
    value=255
)

# Method A: original grayscale.
variants = {
    "grayscale": gray
}

# Method B: Otsu thresholding.
variants["otsu"] = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

# Method C: adaptive thresholding.
variants["adaptive"] = cv2.adaptiveThreshold(
    gray,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31,
    11
)

for name, processed in variants.items():
    cv2.imwrite(
        str(OUTPUT_DIR / f"10_name_{name}.jpg"),
        processed
    )


# ==========================================
# OCR MULTIPLE WAYS
# ==========================================

results = []

for variant_name, processed in variants.items():

    for page_mode in (7, 8, 13):

        config = f"--oem 3 --psm {page_mode}"

        data = pytesseract.image_to_data(
            processed,
            config=config,
            output_type=pytesseract.Output.DICT
        )

        words = []
        confidences = []

        for word, confidence in zip(
            data["text"],
            data["conf"]
        ):
            word = word.strip()

            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                continue

            if word and confidence >= 0:
                words.append(word)
                confidences.append(confidence)

        text = " ".join(words).strip()

        # Avoid accepting an empty result.
        if not text:
            continue

        # Average confidence is a useful comparison,
        # but it does not guarantee the correct name.
        average_confidence = (
            sum(confidences) / len(confidences)
        )

        results.append({
            "text": text,
            "confidence": average_confidence,
            "variant": variant_name,
            "psm": page_mode
        })


# ==========================================
# SHOW OCR CANDIDATES
# ==========================================

print("\n========== OCR CANDIDATES ==========")

if not results:
    print("No text recognised.")
    print("Check output/09_name_original.jpg")
else:
    results.sort(
        key=lambda item: item["confidence"],
        reverse=True
    )

    for result in results:
        print(
            f'{result["text"]} | '
            f'confidence: {result["confidence"]:.1f}% | '
            f'method: {result["variant"]} | '
            f'PSM: {result["psm"]}'
        )

    best = results[0]

    # Basic cleanup: remove unwanted symbols at
    # the start/end while preserving normal MTG
    # name punctuation inside the text.
    cleaned_name = re.sub(
        r"^[^A-Za-z0-9]+|[^A-Za-z0-9)]+$",
        "",
        best["text"]
    ).strip()
    
    print("\n========== BEST CANDIDATE ==========")
    print(f"Recognised name: {cleaned_name}")
    print(f"OCR confidence: {best['confidence']:.1f}%")
    print(f"Preprocessing: {best['variant']}")
    print(f"Page segmentation mode: {best['psm']}")

    # Save the candidates for later debugging.
    with open(
        OUTPUT_DIR / "ocr_candidates.txt",
        "w",
        encoding="utf-8"
    ) as file:
        for result in results:
            file.write(
                f'{result["text"]} | '
                f'{result["confidence"]:.1f}% | '
                f'{result["variant"]} | '
                f'PSM {result["psm"]}\n'
            )
            

    # ==========================================
    # IDENTIFY CARD USING SCRYFALL
    # ==========================================

    print("\nSearching Scryfall...")

    card = lookup_card(cleaned_name)

    if not card:
        print("Card identification was unsuccessful.")

    else:
        scryfall_name = card.get("name", "")

        print(f"OCR name: {cleaned_name}")
        print(f"Scryfall name: {scryfall_name}")

        # Use the official name after Scryfall has identified it.
        cleaned_name = scryfall_name

        print("\nInitial name match:")
        display_card(card)

        print("\n--- Automatic Exact Printing Lookup ---")

        # Extract printing information from the same image
        # used by the title OCR.
        set_code, collector_number = extract_printing_details(image)

        if not set_code or not collector_number:
            print("Could not read both printing details.")
            print("Inspect output/11_bottom_crop.jpg")
            print("and output/12_bottom_ocr.jpg")

        else:
            # Try the printed number first, then remove leading zeros.
            numbers_to_try = [collector_number]
            normalised_number = collector_number.lstrip("0") or "0"

            if normalised_number != collector_number:
                numbers_to_try.append(normalised_number)

            exact_card = None

            for number in numbers_to_try:
                print(
                    f"Trying set={set_code.lower()}, "
                    f"collector number={number}"
                )

                exact_card = lookup_exact_printing(set_code, number)

                if exact_card:
                    break


        # Recover if automatic exact-printing lookup failed.
        if not exact_card:
            print("Exact printing lookup failed.")
            print("The OCR may have misread the set code or collector number.")

            retry = input(
                "Retry with a manually entered set code and collector number? (y/n): "
            ).strip().lower()

            if retry == "y":
                manual_set = input("Enter set code (e.g. IKO): ").strip().lower()
                manual_collector = input(
                    "Enter collector number (e.g. 303): "
                ).strip()

                manual_collector = manual_collector.lstrip("0") or "0"

                exact_card = lookup_exact_printing(
                    manual_set,
                    manual_collector
                )

                if exact_card:
                    print("\nManual printing lookup result:")
                    display_card(exact_card)

                    confirm = input(
                        "Is this the correct printing? (y/n): "
                    ).strip().lower()

                    if confirm != "y":
                        exact_card = None
                        print("Printing rejected.")
                else:
                    print("Manual lookup failed.")

        # Continue whenever we have a card, whether found automatically or manually.
        if exact_card:
            # Verify the card name against the recognised name.
            if exact_card.get("name", "").casefold() != cleaned_name.casefold():
                print("WARNING: The printing does not match the recognised card name.")
                print(f"Recognised name: {cleaned_name}")
                print(f"Returned name: {exact_card.get('name')}")
                print("Card was not added.")

            else:
                print("\nExact printing verified!")
                display_card(exact_card)

                confirmation = input(
                    "\nAdd this card to your inventory? (y/n): "
                ).strip().lower()

                if confirmation == "y":
                    print("\n--- Card Condition ---")
                    print("1. Near Mint")
                    print("2. Lightly Played")
                    print("3. Moderately Played")
                    print("4. Heavily Played")
                    print("5. Damaged")

                    condition_options = {
                        "1": "Near Mint",
                        "2": "Lightly Played",
                        "3": "Moderately Played",
                        "4": "Heavily Played",
                        "5": "Damaged",
                    }

                    while True:
                        condition_choice = input(
                            "Choose condition (1-5, default 1): "
                        ).strip() or "1"

                        if condition_choice in condition_options:
                            condition = condition_options[condition_choice]
                            break

                        print("Invalid choice. Enter a number from 1 to 5.")

                    while True:
                        foil_choice = input(
                            "Is this card foil? (y/n): "
                        ).strip().lower()

                        if foil_choice in ("y", "n"):
                            foil = foil_choice == "y"
                            break

                        print("Please enter y or n.")

                    if os.getenv("INVENTORY_BACKEND", "json").strip().lower() == "mongodb":
                        if not OWNER_ID:
                            raise RuntimeError(
                                "Cannot save to MongoDB: no authenticated owner ID was supplied."
                            )

                        add_card_to_inventory(
                            exact_card,
                            owner_id=OWNER_ID,
                            condition=condition,
                            foil=foil,
                        )
                    else:
                        add_card_to_inventory(
                            exact_card,
                            condition=condition,
                            foil=foil,
                        )
                else:
                    print("Card was not added to inventory.")

                # Save the verified printing information.
                import json

                output_file = OUTPUT_DIR / "identified_card.json"

                with open(output_file, "w", encoding="utf-8") as file:
                    json.dump(
                        exact_card,
                        file,
                        indent=4,
                        ensure_ascii=False
                    )

                print(f"\nVerified card information saved to: {output_file}")

        else:
            print("No verified printing available. Card was not added.")

print("\nDiagnostic images saved in output/.")
