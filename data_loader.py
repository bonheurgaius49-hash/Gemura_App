import pandas as pd
import os

# Set your exact data folder path
DATA_PATH = r"D:\Solid'Africa\OneDrive - SolidAfrica\Python Backend"

def load_all_excel_files():
    """Loads all Excel files in the folder into a dictionary of DataFrames."""
    data_frames = {}
    for file in os.listdir(DATA_PATH):
        if file.endswith(".xlsx"):
            name = file.replace(".xlsx", "")  # filename without extension
            file_path = os.path.join(DATA_PATH, file)
            try:
                data_frames[name] = pd.read_excel(file_path)
                print(f"✅ Loaded {name}: {data_frames[name].shape[0]} rows, {data_frames[name].shape[1]} columns")
            except Exception as e:
                print(f"❌ Error loading {name}: {e}")
    return data_frames

# Example usage
if __name__ == "__main__":
    all_data = load_all_excel_files()
    # Access a table like this:
    # regular_diet = all_data["regular diet"]
    # special_diet = all_data["special diets"]