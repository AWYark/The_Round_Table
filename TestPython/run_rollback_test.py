
from bson import ObjectId
from pathlib import Path

from vendor_booth import complete_marketplace_transaction


ids_file = Path(__file__).with_name("rollback_test_ids.txt")
ids = ids_file.read_text(encoding="utf-8").splitlines()

enquiry_id = ObjectId(ids[3])

complete_marketplace_transaction(
    "vendor_001",
    enquiry_id,
)
