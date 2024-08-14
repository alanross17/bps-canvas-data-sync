import pandas as pd
import glob
import os

def load_and_combine_csv(directory):
    """Load all CSV files in the specified directory and combine them into a single DataFrame."""
    # Build the pattern to match all CSV files
    pattern = os.path.join(directory, '*.csv')
    # List all files that match the pattern
    csv_files = glob.glob(pattern)
    # Load and concatenate all CSV files into a single DataFrame
    df_list = [pd.read_csv(file) for file in csv_files]
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

def load_csv(file_path):
    # Safely load a CSV file into a DataFrame.
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        print(f"Failed to load file {file_path}: {e}")
        return pd.DataFrame()

def preprocess_enrollment_data(file_path):
    # Read the CSV file into a DataFrame
    df = load_and_combine_csv(file_path)
    
    # Initialize an empty list to collect processed rows
    processed_rows = []
    
    # Variables to keep track of the current course details
    current_course_name = None
    current_course_id = None
    current_subject = None
    
    # Iterate over the rows in the DataFrame
    for index, row in df.iterrows():
        if pd.notna(row[1]) and pd.notna(row[2 ]):
            # This row contains course details
            current_course_name = row[0]
            current_course_id = row[1]  # Convert to string without decimal
            current_subject = row[2]
        elif pd.notna(row[3]) and pd.notna(row[5]):
            # This row contains student details
            student_name = row[3]
            student_id = row[5]
            # Append the processed row with course and student details
            processed_rows.append({
                "course_name": current_course_name,
                "course_id": current_course_id,
                "subject": current_subject,
                "name": student_name,
                "user_id": student_id
            })
    
    # Convert the list of processed rows into a DataFrame
    processed_df = pd.DataFrame(processed_rows)

    # clean up data types
    processed_df['user_id'] = processed_df['user_id'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    processed_df['course_id'] = processed_df['course_id'].apply(lambda x: str(int(x)) if pd.notna(x) else x)

    print(processed_df)

    # add status column
    processed_df['type'] = 'student'

    return processed_df

def melt_teachers(df):
    # Drop columns where all entries are NaN which may result from extra commas in the CSV
    df.dropna(axis=1, how='all', inplace=True)
    # Find all columns starting from 'teacher' to the end
    teacher_columns = df.columns[df.columns.get_loc("teacher"):]
    # Melt the DataFrame to have one teacher per row, ignoring empty values
    melted_df = df.melt(id_vars=["course_name", "course_id", "subject"], value_vars=teacher_columns, var_name="Teacher Role", value_name="name")
    melted_df = melted_df.dropna(subset=["name"])  # Remove rows where the teacher name is NaN
    return melted_df[["course_name", "course_id", "subject", "name"]]

def map_teacher_ids(teacher_df, id_df):
    # Create fullname column for mapping
    id_df['fullname'] = id_df['SURNAME'] + ', ' + id_df['NAME']
    id_map = id_df.set_index('fullname')['USER ID'].to_dict()
    # Map user IDs to teacher names
    teacher_df['user_id'] = teacher_df['name'].map(id_map)
    teacher_df['user_id'] = teacher_df['user_id'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    return teacher_df

def preprocess_teacher_enrollments(file_path):
    df = load_and_combine_csv(file_path)
    
    # reformat data
    formatted_df = melt_teachers(df)

    # map user ids
    teacher_ids_df = load_csv('temp_inputs/teacher_ids.csv')
    mapped_df = map_teacher_ids(formatted_df, teacher_ids_df)

    # clean up data type
    mapped_df['user_id'] = mapped_df['user_id'].astype(str)
    mapped_df['course_id'] = mapped_df['course_id'].astype(str)

    # add status column
    mapped_df['type'] = 'teacher'

    return mapped_df



# Load and preprocess the enrollments CSV
enrollments_df = preprocess_enrollment_data('temp_inputs/student_enroll/')

# Load teacher enrollments and teacher IDs
teacher_enroll_df = preprocess_teacher_enrollments('temp_inputs/teacher_enroll/')

# Load the courses CSV file
courses_df = load_csv('temp_inputs/courses.csv')

# Merge teacher and student enrollments
full_enrollment_df = pd.concat([enrollments_df, teacher_enroll_df])
print(full_enrollment_df)

# Format the MS_COURSE_ID and MERGE_CODE without decimals
courses_df['MS_COURSE_ID'] = courses_df['MS_COURSE_ID'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
courses_df['MERGE_CODE'] = courses_df['MERGE_CODE'].apply(lambda x: str(int(x)) if pd.notna(x) else x)

# Create a dictionary to map MS_COURSE_ID to MERGE_CODE
term_map = courses_df.set_index('MS_COURSE_ID')['term_id'].to_dict()
merge_map = courses_df.set_index('MS_COURSE_ID')['MERGE_CODE'].dropna().to_dict()

# Map term_id to each enrollment based on course_id
full_enrollment_df['term_id'] = full_enrollment_df['course_id'].apply(lambda x: term_map.get(x))

# Update enrollments with the MERGE_CODE where applicable
full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(lambda x: merge_map.get(x, x))


# Remove enrollments for courses where CANVAS_NEEDED is "N" or TWO_YEAR_FLAG is "2"
remove_courses = courses_df[(courses_df['CANVAS_NEEDED'] == 'N')]['MS_COURSE_ID']
full_enrollment_df = full_enrollment_df[~full_enrollment_df['course_id'].isin(remove_courses)]

print(full_enrollment_df)

# Format User ID to be prefixed with "u" and 6 digits  
def format_user_id(user_id):
    """Ensure user_id is properly formatted."""
    return f'u{int(user_id):06}' if pd.notna(user_id) else user_id

# Format Course ID to be prefixed with "c" and 6 digits   
def format_course_id(course_id):
    """Ensure course_id is properly formatted."""
    return f'c{int(course_id):06}' if pd.notna(course_id) else course_id

# Apply formatting
full_enrollment_df['user_id'] = full_enrollment_df['user_id'].apply(format_user_id)
full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(format_course_id)

# Add the "type" and "status" columns
full_enrollment_df['status'] = 'active'

# Save separate CSV for each term_id
for term in full_enrollment_df['term_id'].dropna().unique():
    subset = full_enrollment_df[full_enrollment_df['term_id'] == term]
    subset = subset.drop(columns=['subject', 'term_id'])  # Remove specified columns
    subset.to_csv(f'temp_outputs/updated_enrollments_{term}.csv', index=False)

# update courses file:

# Filter out courses where CANVAS_NEEDED does not equal "Y"
courses_df = courses_df[courses_df['CANVAS_NEEDED'] == 'Y']

# Select the specified columns and add the 'status' column with all values set to "active"
selected_columns = ['long_name', 'short_name', 'status', 'course_id', 'account_id', 'term_id', 'blueprint_course_id']
courses_df = courses_df[selected_columns[:-1]]  # Exclude 'status' initially since it's not in the original DataFrame
courses_df['status'] = 'active'  # Add 'status' with all entries set to "active"

# Save the filtered data to a new CSV file
courses_df.to_csv('temp_outputs/updated_courses.csv', index=False)