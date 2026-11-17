
import os

backend = os.getenv("INVENTORY_BACKEND", "json").strip().lower()

if backend == "mongodb":
    from mongo_inventory import add_card_to_inventory
elif backend == "json":
    from inventory import add_card_to_inventory
else:
    raise ValueError(
        "Invalid INVENTORY_BACKEND. Choose 'json' or 'mongodb'."
    )

print(f"Inventory storage: {backend}")
