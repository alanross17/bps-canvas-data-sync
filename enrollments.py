import pandas as pd
import glob
import os

### =================
### CSV File Handling
### =================

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

### =================================
### Student Enrollments Preprocessing
### =================================

def preprocess_enrollment_data(file_path):
    """
    Preprocesses enrollment data from a CSV file.

    Args:
        file_path (str): Path to the CSV file containing enrollment data.

    Returns:
        pd.DataFrame: Processed DataFrame with course and student details.
    """
    # Read the CSV file into a DataFrame
    df = load_and_combine_csv(file_path)
    
    # Initialize variables for current course details
    current_course = {
        "name": None,
        "id": None,
        "subject": None
    }
    
    # List to collect processed rows
    processed_rows = []

    # Iterate over the rows in the DataFrame
    for _, row in df.iterrows():
        if pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
            # Update current course details
            current_course = {
                "name": row.iloc[0],
                "id": str(int(row.iloc[1])),
                "subject": row.iloc[2]
            }
        elif pd.notna(row.iloc[3]) and pd.notna(row.iloc[5]):
            # Append processed row with course and student details
            processed_rows.append({
                "course_name": current_course["name"],
                "course_id": current_course["id"],
                "subject": current_course["subject"],
                "name": row.iloc[3],
                "user_id": str(int(row.iloc[5]))
            })
    
    # Convert the list of processed rows into a DataFrame
    processed_df = pd.DataFrame(processed_rows)

    # Add status column
    processed_df['type'] = 'student'
    
    return processed_df

### =================================
### Teacher Enrollments Preprocessing
### =================================
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
    mapped_df['role'] = 'teacher'

    return mapped_df


### ===============
### Main Processing
### ===============

def load_and_preprocess_data():
    """
    Load and preprocess the student and teacher enrollment data,
    and load the courses data.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: DataFrame with student enrollments.
            - pd.DataFrame: DataFrame with teacher enrollments.
            - pd.DataFrame: DataFrame with course information.
    """
    enrollments_df = preprocess_enrollment_data('temp_inputs/student_enroll/')
    teacher_enroll_df = preprocess_teacher_enrollments('temp_inputs/teacher_enroll/')
    courses_df = load_csv('temp_inputs/courses.csv')
    return enrollments_df, teacher_enroll_df, courses_df

def format_course_data(courses_df):
    """
    Format course data, including course IDs and merge codes.
    Creates mappings for term_id and MERGE_CODE.

    Args:
        courses_df (pd.DataFrame): DataFrame containing course information.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The formatted courses DataFrame.
            - dict: Mapping of MS_COURSE_ID to term_id.
            - dict: Mapping of MS_COURSE_ID to MERGE_CODE.
    """
    # Format MS_COURSE_ID and MERGE_CODE columns to remove decimals
    courses_df['MS_COURSE_ID'] = courses_df['MS_COURSE_ID'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    courses_df['MERGE_CODE'] = courses_df['MERGE_CODE'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    
    # Create mappings for term_id and MERGE_CODE
    term_map = courses_df.set_index('MS_COURSE_ID')['term_id'].to_dict()
    merge_map = courses_df.set_index('MS_COURSE_ID')['MERGE_CODE'].dropna().to_dict()
    
    return courses_df, term_map, merge_map

def update_enrollments(full_enrollment_df, courses_df, term_map, merge_map):
    """
    Update enrollment data with term_id and merge_code.
    Removes enrollments for courses that do not need Canvas or have a two-year flag.

    Args:
        full_enrollment_df (pd.DataFrame): DataFrame with combined enrollments.
        courses_df (pd.DataFrame): DataFrame with course information.
        term_map (dict): Mapping of MS_COURSE_ID to term_id.
        merge_map (dict): Mapping of MS_COURSE_ID to MERGE_CODE.

    Returns:
        pd.DataFrame: Updated DataFrame with term_id and filtered enrollments.
    """
    # Map term_id to each enrollment based on course_id
    full_enrollment_df['term_id'] = full_enrollment_df['course_id'].apply(lambda x: term_map.get(x))
    
    # Update course_id with MERGE_CODE where applicable
    full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(lambda x: merge_map.get(x, x))
    
    # Remove enrollments for courses where CANVAS_NEEDED is "N" or TWO_YEAR_FLAG is "2"
    remove_courses = courses_df[courses_df['CANVAS_NEEDED'] == 'N']['MS_COURSE_ID']
    full_enrollment_df = full_enrollment_df[~full_enrollment_df['course_id'].isin(remove_courses)]
    
    return full_enrollment_df

def format_ids(full_enrollment_df):
    """
    Format user_id and course_id to specific formats.

    Args:
        full_enrollment_df (pd.DataFrame): DataFrame with enrollment information.

    Returns:
        pd.DataFrame: Updated DataFrame with formatted user_id and course_id.
    """

    def format_user_id(user_id):
        """
        Format user_id to be prefixed with "u" and 6 digits.

        Args:
            user_id (str or int): User ID to format.

        Returns:
            str: Formatted user ID.
        """
        return f'u{int(user_id):06}' if pd.notna(user_id) else user_id
    

    def format_course_id(course_id):
        """
        Format course_id to be prefixed with "c" and 6 digits.

        Args:
            course_id (str or int): Course ID to format.

        Returns:
            str: Formatted course ID.
        """
        return f'c{int(course_id):06}' if pd.notna(course_id) else course_id

    # Apply formatting to user_id and course_id columns
    full_enrollment_df['user_id'] = full_enrollment_df['user_id'].apply(format_user_id)
    full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(format_course_id)
    
    # Add status column with default value 'active'
    full_enrollment_df['status'] = 'active'
    
    return full_enrollment_df

def save_enrollments_by_term(full_enrollment_df):
    """
    Save separate CSV files for each term_id.

    Args:
        full_enrollment_df (pd.DataFrame): DataFrame with term-specific enrollments.
    """
    # Save separate CSV for each unique term_id
    for term in full_enrollment_df['term_id'].dropna().unique():
        # Create directory path for the term
        output_dir = f'temp_outputs/enrollments_{term}'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Define the file path for saving the CSV
        file_path = os.path.join(output_dir, 'enrollments.csv')
        
        # Drop unnecessary columns and save the CSV
        subset = full_enrollment_df[full_enrollment_df['term_id'] == term].drop(columns=['subject', 'term_id'])
        subset.to_csv(file_path, index=False)


def update_and_save_courses(courses_df):
    """
    Filter and save the courses data.

    Args:
        courses_df (pd.DataFrame): DataFrame with course information.
    """
    # Filter out courses where CANVAS_NEEDED is not "Y"
    courses_df = courses_df[courses_df['CANVAS_NEEDED'] == 'Y']
    
    # Select relevant columns and add 'status' column
    selected_columns = ['long_name', 'short_name', 'status', 'course_id', 'account_id', 'term_id', 'blueprint_course_id']
    courses_df = courses_df[selected_columns]
    
    # Save the filtered data to a new CSV file
    courses_df.to_csv('temp_outputs/courses.csv', index=False)


def main():
    """
    Main function to load, process, and save enrollment and course data.
    """
    # Load and preprocess data
    enrollments_df, teacher_enroll_df, courses_df = load_and_preprocess_data()

    # Combine student and teacher enrollments
    full_enrollment_df = pd.concat([enrollments_df, teacher_enroll_df])

    # Format course data and create mappings
    courses_df, term_map, merge_map = format_course_data(courses_df)
    
    # Update enrollments with term_id and merge_code
    full_enrollment_df = update_enrollments(full_enrollment_df, courses_df, term_map, merge_map)
    
    # Format IDs and add status column
    full_enrollment_df = format_ids(full_enrollment_df)
    
    # Save enrollments by term
    save_enrollments_by_term(full_enrollment_df)
    
    # Update and save course data
    update_and_save_courses(courses_df)

if __name__ == "__main__":
    main()
