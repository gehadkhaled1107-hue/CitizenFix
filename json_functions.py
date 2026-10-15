import json
import os


def load_data(file_path, default_return=None):
    if default_return is None:
        default_return = []  

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"Error: '{file_path}' contains corrupted data.")
            return default_return
        except Exception as e:
            print(f"Error reading '{file_path}': {e}")
            return default_return

    return default_return


def save_data(data, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving data to '{file_path}': {e}")
