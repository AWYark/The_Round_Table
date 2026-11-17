# OCR Setup – The Round Table

## 1. Overview

The Round Table uses Tesseract OCR to recognise Magic: The Gathering card information from images.

The application uses:
- Tesseract OCR 5.5.3
- pytesseract 0.3.13
- OpenCV 5.0.0.93
- Pillow 10.4.0
- NumPy 2.4.6

## 2. Install Tesseract OCR

The development environment used Windows with:

Tesseract version: 5.5.3.20260724

Download a Windows installer from:
https://github.com/UB-Mannheim/tesseract/wiki

Install Tesseract OCR.

The development installation location was:

C:\Program Files\Tesseract-OCR\tesseract.exe

Ensure English language data (eng.traineddata) is installed.

## 3. Verify installation

Open PowerShell and execute:

    tesseract --version

Expected version:

    tesseract v5.5.3.20260724

Check the executable location:

    where.exe tesseract

## 4. Python integration

The application uses pytesseract as the Python interface to the Tesseract engine.

Install Python dependencies from the project root:

    python -m pip install -r requirements.txt

The main scanner currently configures the executable in scanner2.py:

    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

If Tesseract is installed in a different directory, update this path to match the local installation.

## 5. Test OCR

Run:

    tesseract --version

Then launch the application:

    python ui_app.py

Select an appropriate card image and test the scanner.

## 6. Troubleshooting

### TesseractNotFoundError

Check that Tesseract is installed and that the executable path in scanner2.py is correct.

### Language data errors

Confirm that English language data (eng.traineddata) is installed in the Tesseract tessdata directory.

### Poor OCR results

Use a clear, well-lit card image. Avoid blur, reflections, and excessive image compression.

## 7. Platform considerations

These instructions describe the verified Windows desktop development environment.

The Windows Tesseract executable cannot be used directly inside an Android APK.

Android requires a separately configured Android-compatible OCR engine and packaging solution. Android OCR packaging and validation should be treated as a separate deployment task.
