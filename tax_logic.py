#V2

import json
import os

DATA_FILE = "tax_data.json"

def load_data():
    """Loads client payments and expenses from the local JSON database."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"earnings": [], "expenses": []}
    return {"earnings": [], "expenses": []}

def save_data(data):
    """Saves client payments and expenses to the local JSON database."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def reset_data():
    """Resets the local database to empty lists."""
    empty_data = {"earnings": [], "expenses": []}
    save_data(empty_data)
    return empty_data