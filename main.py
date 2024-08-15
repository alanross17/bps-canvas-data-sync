import pandas as pd
import os
from dotenv import load_dotenv
from student_preprocessing import preprocess_enrollment_data
from teacher_preprocessing import preprocess_teacher_enrollments
from file_handling import load_csv
from course_preprocessing import format_course_data, update_enrollments, format_ids, update_and_save_courses
from api_posting import post_csv_to_api

def load_and_preprocess_data():
    enrollments_df = preprocess_enrollment_data('temp_inputs/student_enroll/')
    teacher_enroll_df = preprocess_teacher_enrollments('temp_inputs/teacher_enroll/')
    courses_df = load_csv('temp_inputs/courses.csv')
    return enrollments_df, teacher_enroll_df, courses_df

# def save_enrollments_by_term(full_enrollment_df, token, canvas_url, account_id):
#     for term in full_enrollment_df['term_id'].dropna().unique():
#         output_dir = f'temp_outputs/enrollments_{term}'
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)
#         file_path = os.path.join(output_dir, 'enrollments.csv')
#         subset = full_enrollment_df[full_enrollment_df['term_id'] == term].drop(columns=['subject', 'term_id'])
#         subset.to_csv(file_path, index=False)
        
#         # Post the CSV file to the API
#         response = post_csv_to_api(file_path, token, canvas_url, account_id)
#         print(f"Posted {file_path} to API. Response: {response.status_code}")

def save_enrollments_by_term(full_enrollment_df, token, canvas_url, account_id):
    for term in full_enrollment_df['term_id'].dropna().unique():
        if term == 'BPS_DP24':
            output_dir = f'temp_outputs/enrollments_{term}'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            file_path = os.path.join(output_dir, 'enrollments.csv')
            subset = full_enrollment_df[full_enrollment_df['term_id'] == term].drop(columns=['subject', 'term_id'])
            subset.to_csv(file_path, index=False)
            
            # Post the CSV file to the API
            response = post_csv_to_api(file_path, token, canvas_url, account_id)
            print(f"Posted {file_path} to API. Response: {response.status_code}")
        else:
            print(f"Skipping term {term}")

def main():
    load_dotenv()  # Load environment variables from .env file
    enrollments_df, teacher_enroll_df, courses_df = load_and_preprocess_data()
    full_enrollment_df = pd.concat([enrollments_df, teacher_enroll_df])
    courses_df, term_map, merge_map = format_course_data(courses_df)
    full_enrollment_df = update_enrollments(full_enrollment_df, courses_df, term_map, merge_map)
    full_enrollment_df = format_ids(full_enrollment_df)
    
    # Load the API credentials and other parameters from environment variables
    token = os.getenv('CANVAS_API_TOKEN')
    canvas_url = os.getenv('CANVAS_URL')
    account_id = os.getenv('CANVAS_ACCOUNT_ID')
    
    save_enrollments_by_term(full_enrollment_df, token, canvas_url, account_id)
    update_and_save_courses(courses_df)

if __name__ == "__main__":
    main()