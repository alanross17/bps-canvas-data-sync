import pandas as pd
import os
from student_preprocessing import preprocess_enrollment_data
from teacher_preprocessing import preprocess_teacher_enrollments
from file_handling import load_csv
from course_preprocessing import format_course_data, update_enrollments, format_ids, update_and_save_courses

def load_and_preprocess_data():
    enrollments_df = preprocess_enrollment_data('temp_inputs/student_enroll/')
    teacher_enroll_df = preprocess_teacher_enrollments('temp_inputs/teacher_enroll/')
    courses_df = load_csv('temp_inputs/courses.csv')
    return enrollments_df, teacher_enroll_df, courses_df

def save_enrollments_by_term(full_enrollment_df):
    for term in full_enrollment_df['term_id'].dropna().unique():
        output_dir = f'temp_outputs/enrollments_{term}'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file_path = os.path.join(output_dir, 'enrollments.csv')
        subset = full_enrollment_df[full_enrollment_df['term_id'] == term].drop(columns=['subject', 'term_id'])
        subset.to_csv(file_path, index=False)

def main():
    enrollments_df, teacher_enroll_df, courses_df = load_and_preprocess_data()
    full_enrollment_df = pd.concat([enrollments_df, teacher_enroll_df])
    courses_df, term_map, merge_map = format_course_data(courses_df)
    full_enrollment_df = update_enrollments(full_enrollment_df, courses_df, term_map, merge_map)
    full_enrollment_df = format_ids(full_enrollment_df)
    save_enrollments_by_term(full_enrollment_df)
    update_and_save_courses(courses_df)

if __name__ == "__main__":
    main()