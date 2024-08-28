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

def save_enrollments_by_term(full_enrollment_df, token, canvas_url, account_id, selected_terms):
    for term in full_enrollment_df['term_id'].dropna().unique():
        output_dir = f'temp_outputs/enrollments_{term}'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file_path = os.path.join(output_dir, 'enrollments.csv')
        subset = full_enrollment_df[full_enrollment_df['term_id'] == term].drop(columns=['subject', 'term_id'])
        subset.to_csv(file_path, index=False)

        print(f"CSV file created: {file_path}")

        if term in selected_terms:
            # Post the CSV file to the API
            response = post_csv_to_api(file_path, token, canvas_url, account_id)
            print(f"Posted {file_path} to API. Response: {response.status_code} - {response.text}")
        else:
            print(f"Skipping API post for term {term}")

def get_user_selected_terms(available_terms):
    print("Available terms:")
    for i, term in enumerate(available_terms, start=1):
        print(f"{i}: {term}")
    
    selected_indexes = input("Enter the numbers of the terms you want to POST to the API (comma separated, e.g., 1,3): ")
    selected_indexes = selected_indexes.split(',')
    
    selected_terms = [available_terms[int(index.strip()) - 1] for index in selected_indexes if index.strip().isdigit() and 1 <= int(index.strip()) <= len(available_terms)]
    
    return selected_terms

def main():
    load_dotenv()  # Load environment variables from .env file
    enrollments_df, teacher_enroll_df, courses_df = load_and_preprocess_data()
    full_enrollment_df = pd.concat([enrollments_df, teacher_enroll_df])
    courses_df, term_map, merge_map = format_course_data(courses_df)
    full_enrollment_df = update_enrollments(full_enrollment_df, courses_df, term_map, merge_map)
    full_enrollment_df = format_ids(full_enrollment_df)

    # Get the list of available terms
    available_terms = sorted(full_enrollment_df['term_id'].dropna().unique())
    
    # Get user-selected terms for posting
    selected_terms = get_user_selected_terms(available_terms)
    
    # Load the API credentials and other parameters from environment variables
    token = os.getenv('CANVAS_API_TOKEN')
    canvas_url = os.getenv('CANVAS_URL')
    account_id = os.getenv('CANVAS_ACCOUNT_ID')
    
    save_enrollments_by_term(full_enrollment_df, token, canvas_url, account_id, selected_terms)
    update_and_save_courses(courses_df)

if __name__ == "__main__":
    main()