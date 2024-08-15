import pandas as pd
import glob
import os

def load_and_combine_csv(directory):
    """Load all CSV files in the specified directory and combine them into a single DataFrame."""
    pattern = os.path.join(directory, '*.csv')
    csv_files = glob.glob(pattern)
    df_list = [pd.read_csv(file) for file in csv_files]
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

def load_csv(file_path):
    """Safely load a CSV file into a DataFrame."""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        print(f"Failed to load file {file_path}: {e}")
        return pd.DataFrame()