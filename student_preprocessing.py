import pandas as pd
from file_handling import load_and_combine_csv

def preprocess_enrollment_data(file_path):
    """Preprocesses enrollment data from a CSV file."""
    df = load_and_combine_csv(file_path)
    current_course = {"name": None, "id": None, "subject": None}
    processed_rows = []

    for _, row in df.iterrows():
        if pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
            current_course = {
                "name": row.iloc[0],
                "id": str(int(row.iloc[1])),
                "subject": row.iloc[2]
            }
        elif pd.notna(row.iloc[3]) and pd.notna(row.iloc[5]):
            processed_rows.append({
                "course_name": current_course["name"],
                "course_id": current_course["id"],
                "subject": current_course["subject"],
                "name": row.iloc[3],
                "user_id": str(int(row.iloc[5]))
            })

    processed_df = pd.DataFrame(processed_rows)
    processed_df['type'] = 'student'
    return processed_df