import pandas as pd

def preprocess_enrollment_data(file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, header=None)
    
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
    return processed_df

def preprocess_teacher_enrollments(file_path):
    df = pd.read_csv(file_path)
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

# Load and preprocess the enrollments CSV
enrollments_df = preprocess_enrollment_data('enrollments.csv')
enrollments_df['user_id'] = enrollments_df['user_id'].astype(str)
enrollments_df['type'] = 'student'

# Load teacher enrollments and teacher IDs
teacher_enroll_df = preprocess_teacher_enrollments('teacher_enroll.csv')
teacher_ids_df = pd.read_csv('teacher_ids.csv')
teacher_enroll_df = map_teacher_ids(teacher_enroll_df, teacher_ids_df)
teacher_enroll_df['user_id'] = teacher_enroll_df['user_id'].astype(str)
teacher_enroll_df['course_id'] = teacher_enroll_df['course_id'].astype(str)
teacher_enroll_df['type'] = 'teacher'

# Load the courses CSV file
courses_df = pd.read_csv('courses.csv')

# Merge teacher and student enrollments
full_enrollment_df = pd.concat([enrollments_df, teacher_enroll_df])

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
#remove_courses = courses_df[(courses_df['CANVAS_NEEDED'] == 'N') | (courses_df['CANVAS_NEEDED'] == 2)]['MS_COURSE_ID']
full_enrollment_df = full_enrollment_df[~full_enrollment_df['course_id'].isin(remove_courses)]

def format_student_id(user_id):
    # Check if user_id is a string and not NaN
    if pd.notna(user_id) and isinstance(user_id, str):
        if user_id.startswith('u'):
            return user_id  # If already properly formatted, return as is
        elif len(user_id) <= 6:
            return f'u{int(user_id):06}'  # Format as 'u' followed by six digits
    elif pd.notna(user_id):
        # Handle numeric user_ids that might have been interpreted as float/int
        user_id = str(int(user_id))  # Convert to string, assuming it's a valid integer
        return f'u{int(user_id):06}'
    return user_id  # Return as is if it doesn't fit the criteria or is NaN

# Format Course ID to be prefixed with "c" and 6 digits   
def format_course_id(course_id):
    if course_id.startswith('c'): # If already properly formatted, return as is
        return course_id
    elif len(course_id) <= 6:
        return f'c{int(course_id):06}' # Assuming course IDs should start with "u"
    else:
        return course_id # Return as is if doesn't fit the criteria

# Apply formatting
full_enrollment_df['user_id'] = full_enrollment_df['user_id'].apply(format_student_id)
full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(format_course_id)

# Add the "type" and "status" columns
#full_enrollment_df['type'] = 'student'
full_enrollment_df['status'] = 'active'

# Save separate CSV for each term_id
for term in full_enrollment_df['term_id'].dropna().unique():
    subset = full_enrollment_df[full_enrollment_df['term_id'] == term]
    subset = subset.drop(columns=['subject', 'term_id'])  # Remove specified columns
    subset.to_csv(f'updated_enrollments_{term}.csv', index=False)

# update courses file:

# Filter out courses where CANVAS_NEEDED does not equal "Y"
courses_df = courses_df[courses_df['CANVAS_NEEDED'] == 'Y']

# Select the specified columns and add the 'status' column with all values set to "active"
selected_columns = ['long_name', 'short_name', 'status', 'course_id', 'account_id', 'term_id', 'blueprint_course_id']
courses_df = courses_df[selected_columns[:-1]]  # Exclude 'status' initially since it's not in the original DataFrame
courses_df['status'] = 'active'  # Add 'status' with all entries set to "active"

# Save the filtered data to a new CSV file
courses_df.to_csv('updated_courses.csv', index=False)