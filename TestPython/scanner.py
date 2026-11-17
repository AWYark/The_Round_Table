import cv2
import numpy as np
import pytesseract
import os

#tells python where Tesseract is Installed
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

#file paths
image_path = "images/Xyris-the-Writhing-Storm.jpg"

output_dir = "output"

os.makedirs(output_dir, exist_ok=True)

#load Image
image = cv2.imread(image_path)

if image is None:
    print(f"Error: Could not load image from {image_path}")
    exit(1)
    
print("Image loaded successfully.")

cv2.imwrite(
    f"{output_dir}/original_image.jpg", image
)

#resize Image
height, width = image.shape[:2]

max_width = 1200

if width > max_width:

    scale = max_width / width

    image = cv2.resize(
        image,
        (
            max_width,
            int(height * scale)
        )
    )

cv2.imwrite(f"{output_dir}/02_resized.jpg", image)

#converts the image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

cv2.imwrite(f"{output_dir}/03_grayscale.jpg", gray)

#blurs the image to reduce noise and improve OCR accuracy
blur = cv2.GaussianBlur(gray, (7, 7), 0)

#edge detection using Canny
edges = cv2.Canny(blur, 30, 100)

cv2.imwrite(f"{output_dir}/04_edges.jpg", edges)

#morphological processing
kernel = cv2.getStructuringElement(
    cv2.MORPH_RECT,
    (5, 5)
)

edges_closed = cv2.morphologyEx(
    edges,
    cv2.MORPH_CLOSE,
    kernel,
    iterations=2
)

cv2.imwrite(
    f"{output_dir}/04_edges_closed.jpg",
    edges_closed
)

#find contours in the edge-detected image
contours, _ = cv2.findContours(edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

image_area = image.shape[0] * image.shape[1]

candidates = []

#find rectangular card
for contour in contours:

    area = cv2.contourArea(contour)

    # Ignore very small objects
    if area < image_area * 0.10:
        continue

    perimeter = cv2.arcLength(
        contour,
        True
    )

    approximation = cv2.approxPolyDP(
        contour,
        0.04 * perimeter,
        True
    )

    x, y, w, h = cv2.boundingRect(contour)

    if h == 0 or w == 0:
        continue

    aspect_ratio = w / h

    # MTG card ratio is approximately 0.716
    # but perspective can change this considerably.
    if 0.50 < aspect_ratio < 0.90:

        candidates.append(
            (
                area,
                approximation,
                x,
                y,
                w,
                h
            )
        )

#check if any candidates were found
if not candidates:
    print("Could not automatically detect the card")
    
    print("Try taking a photo with the card clearly seperated from the background")
    
    exit()
    
#choose largest candidtae
candidates.sort(key=lambda item: item[0], reverse=True)

area, contour, x, y, w, h = candidates[0]

print(f"possible MTG card Detected. Area: {area:.0f} pixels")

#draw detected card boundary
detected = image.copy()

cv2.rectangle(detected, (x, y), (x + w, y + h), (0, 255, 0), 5)

cv2.imwrite(f"{output_dir}/05_detected.jpg", detected)

#crop card name

card = image[y:y + h, x:x + w]

cv2.imwrite(f"{output_dir}/06_card_crop.jpg", card)

print("Card cropped successfully.")

#approximate coordinates for the card name area

card_hight, card_width = card.shape[:2]

#topporiion of the card where the name is located
name_top = int(card_hight * 0.035)
name_bottom = int(card_hight * 0.09)

name_left = int(card_width * 0.045)
name_right = int(card_width * 0.95)

name_crop = card[name_top:name_bottom, name_left:name_right]

cv2.imwrite(f"{output_dir}/07_name_crop.jpg", name_crop) 

#prep name for tesserect OCR
name_gray = cv2.cvtColor(name_crop, cv2.COLOR_BGR2GRAY)

#enlarge image
name_gray = cv2.resize(name_gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

#improve contrast
name_gray = cv2.GaussianBlur(name_gray, (3, 3), 0)

#threshold
name_threshold = cv2.threshold(name_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

cv2.imwrite(f"{output_dir}/08_name_processed.jpg", name_threshold)

#OCR
card_name = pytesseract.image_to_string(name_threshold, config="--psm 7")

# #crop card text
# #approximate coordinates for the card text area
# collector_crop = wraped[850:1030, 40:704]

# cv2.imwrite(f"{output_dir}/08_collector_crop.jpg", collector_crop)

# #OCR card name
# name_gray = cv2.cvtColor(name_crop, cv2.COLOR_BGR2GRAY)

# name_gray = cv2.resize(name_gray,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)

# name_gray = cv2.threshold(name_gray,0,255,cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# card_name = pytesseract.image_to_string(name_gray, config="--psm 7")

# #OCR collector information
# collector_gray = cv2.cvtColor(collector_crop, cv2.COLOR_BGR2GRAY)

# collector_gray = cv2.resize(collector_gray,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)

# collector_gray = cv2.threshold(collector_gray,0,255,cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# collector_info = pytesseract.image_to_string(collector_gray, config="--psm 6")


print("\n===== OCR Results =====\n")
print(f"Card Name: {card_name.strip()}")
# print(f"Collector Info: {collector_info}")
print("\n======================\n")