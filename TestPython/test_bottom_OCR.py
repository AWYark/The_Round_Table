from scryfall_lookup import lookup_exact_printing, display_card
import json
from pathlib import Path

import cv2
import pytesseract
import re

# Change this to the filename of your card image in images/.
BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "images" / "Xyris-the-Writhing-Storm.jpg"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the card image.
image = cv2.imread(str(IMAGE_PATH))

if image is None:
    raise FileNotFoundError(
        f"Could not load image: {IMAGE_PATH}\n"
        "Check the filename and images folder."
    )

height, width = image.shape[:2]
print(f"Image dimensions: {width} x {height}")

# Crop the bottom-left area containing collector number and set code.
x1 = int(width * 0.04)
x2 = int(width * 0.52)
y1 = int(height * 0.935)
y2 = int(height * 0.985)

crop = image[y1:y2, x1:x2]

# Enlarge the crop to help Tesseract read small text.
enlarged = cv2.resize(
    crop,
    None,
    fx=4,
    fy=4,
    interpolation=cv2.INTER_CUBIC
)

gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

# Apply thresholding to make the text stand out.
_, thresholded = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

# Save the diagnostic images.
cv2.imwrite(str(OUTPUT_DIR / "bottom_crop.jpg"), crop)
cv2.imwrite(str(OUTPUT_DIR / "bottom_enlarged.jpg"), enlarged)
cv2.imwrite(str(OUTPUT_DIR / "bottom_threshold.jpg"), thresholded)

# Read the cropped text.
config = "--oem 3 --psm 6"

text = pytesseract.image_to_string(
    thresholded,
    config=config
)

print("\n========== BOTTOM OCR RESULT ==========")
print(text)
print("=======================================")

# Extract the collector number from text such as 018/322 but removes the leading zero.
number_match = re.search(
    r"\b(\d{1,4}[a-zA-Z]?)\s*/\s*\d{1,4}\b",
    text
)
if number_match:
    collector_number = number_match.group(1).lstrip("0") or "0"
else:
    collector_number = None

# Extract a set code such as C20.
# This pattern is suitable for the current C20 test card.
set_match = re.search(
    r"\b([A-Z0-9]{2,6})\s*[*★]",
    text.upper()
)

collector_number = number_match.group(1) if number_match else None
set_code = set_match.group(1) if set_match else None

print("\n========== EXTRACTED CARD DETAILS ==========")
print(f"Collector number: {collector_number}")
print(f"Set code: {set_code}")
print("============================================")



if collector_number and set_code:
    print("\nLooking up exact printing on Scryfall...")

    # Try the printed number first, then remove leading zeros.
    numbers_to_try = [collector_number]
    normalised_number = collector_number.lstrip("0") or "0"

    if normalised_number != collector_number:
        numbers_to_try.append(normalised_number)

    exact_card = None

    for number in numbers_to_try:
        print(f"Trying set={set_code.lower()}, number={number}")

        exact_card = lookup_exact_printing(set_code, number)

        if exact_card:
            break

    if exact_card:
        # Verify the API result matches the requested set and card number.
        if (
            exact_card.get("set", "").lower() != set_code.lower()
            or exact_card.get("collector_number", "") not in numbers_to_try
        ):
            print("Warning: returned card details do not match the requested printing.")
        else:
            display_card(exact_card)

            output_file = OUTPUT_DIR / "identified_card.json"

            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(
                    exact_card,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            print(f"\nSaved exact printing to: {output_file}")
    else:
        print("Exact-printing lookup failed for both number formats.")
else:
    print("Missing set code or collector number.")
