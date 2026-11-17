
from bson import ObjectId
from pathlib import Path
from vendor_booth import complete_marketplace_transaction

ids_file = Path(__file__).with_name("production_purchase_test_ids.txt")

if not ids_file.exists():
    raise SystemExit(
        "Test IDs not found. Run setup_production_purchase_test.py first."
    )

ids = ids_file.read_text(encoding="utf-8").splitlines()

if len(ids) != 3:
    raise SystemExit("Test ID file is incomplete.")

test_enquiry_id = ObjectId(ids[2])
seller_owner_id = "vendor_001"

complete_marketplace_transaction(
    seller_owner_id,
    test_enquiry_id,
)
