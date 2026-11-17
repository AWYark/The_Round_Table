# The Round Table
## Regional Trading Card Inventory and Marketplace Application

The Round Table is a Magic: The Gathering collection management and marketplace application developed using Python and Kivy.

The project aims to help users manage card collections, identify cards through image recognition, view card information and values, and interact with marketplace functionality.

## Main Features

- User registration and authentication
- Personal card inventory management
- Card image scanning using OCR
- Card identification and information lookup
- Card valuation and currency conversion
- Vendor booth and marketplace functionality
- Purchase and inventory quantity management
- MongoDB Atlas database integration

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.11.9 |
| GUI framework | Kivy 2.3.2 |
| Database | MongoDB Atlas |
| Database driver | PyMongo 4.19.0 |
| OCR engine | Tesseract 5.5.3 |
| OCR Python wrapper | pytesseract 0.3.13 |
| Image processing | OpenCV and Pillow |

## Requirements

- Windows computer for the documented desktop setup
- Python 3.11.9
- Git
- Tesseract OCR 5
- MongoDB Atlas account and database access

## Installation

### 1. Clone the repository

    git clone https://github.com/AWYark/The_Round_Table.git

    cd The_Round_Table

### 2. Create a virtual environment

    python -m venv .venv

Activate it in PowerShell:

    .\.venv\Scripts\Activate.ps1

### 3. Install dependencies

    python -m pip install --upgrade pip

    python -m pip install -r requirements.txt

### 4. Install Tesseract OCR

Follow the instructions in:

    docs/OCR_SETUP.md

The development environment used Tesseract 5.5.3.

### 5. Configure MongoDB Atlas

Copy the environment template:

    Copy-Item .env.example .env

Open .env and replace the placeholder with your MongoDB Atlas connection string:

    MONGODB_URI=your_actual_connection_string

A MongoDB Atlas database user and appropriate network access permissions are required.

Never upload the actual .env file to GitHub.

### 6. Run the application

From the project root:

    python ui_app.py

## Project Structure

    The_Round_Table/
    |
    |-- authentication.py
    |-- card_summary.py
    |-- database.py
    |-- inventory.py
    |-- inventory_store.py
    |-- main.py
    |-- mongo_inventory.py
    |-- refresh_price.py
    |-- scanner2.py
    |-- scryfall_lookup.py
    |-- ui_app.py
    |-- vendor_booth.py
    |-- view_inventory.py
    |
    |-- images/
    |-- TestPython/
    |-- docs/
    |
    |-- requirements.txt
    |-- .env.example
    |-- .gitignore

## Testing

The TestPython directory contains test scripts, database utilities, migration scripts and marketplace transaction verification scripts.

Review each script before running it.

Some scripts interact with database records. Use dedicated test accounts and test data rather than an ordinary production account.

## Database

The application uses MongoDB Atlas.

The database name is:

    the_round_table

Collections include:

- inventory
- marketplace_enquiries
- users

## Android Development

Android packaging is being developed separately using Buildozer and python-for-android.

The Windows desktop setup instructions do not represent a completed Android installation.

Android packaging and device validation remain separate deployment requirements.

## Security

- MongoDB credentials are stored in a local .env file.
- The .env file is excluded from Git.
- Never publish database passwords, API keys or access tokens.
- Use dedicated test accounts when testing transactions.

## Repository

GitHub:

https://github.com/AWYark/The_Round_Table
