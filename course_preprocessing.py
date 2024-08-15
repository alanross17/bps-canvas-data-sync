import pandas as pd

def format_course_data(courses_df):
    courses_df['MS_COURSE_ID'] = courses_df['MS_COURSE_ID'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    courses_df['MERGE_CODE'] = courses_df['MERGE_CODE'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    term_map = courses_df.set_index('MS_COURSE_ID')['term_id'].to_dict()
    merge_map = courses_df.set_index('MS_COURSE_ID')['MERGE_CODE'].dropna().to_dict()
    return courses_df, term_map, merge_map

def update_enrollments(full_enrollment_df, courses_df, term_map, merge_map):
    full_enrollment_df['term_id'] = full_enrollment_df['course_id'].apply(lambda x: term_map.get(x))
    full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(lambda x: merge_map.get(x, x))
    remove_courses = courses_df[courses_df['CANVAS_NEEDED'] == 'N']['MS_COURSE_ID']
    full_enrollment_df = full_enrollment_df[~full_enrollment_df['course_id'].isin(remove_courses)]
    return full_enrollment_df

def format_ids(full_enrollment_df):
    def format_user_id(user_id):
        return f'u{int(user_id):06}' if pd.notna(user_id) else user_id

    def format_course_id(course_id):
        return f'c{int(course_id):06}' if pd.notna(course_id) else course_id

    full_enrollment_df['user_id'] = full_enrollment_df['user_id'].apply(format_user_id)
    full_enrollment_df['course_id'] = full_enrollment_df['course_id'].apply(format_course_id)
    full_enrollment_df['status'] = 'active'
    return full_enrollment_df

def update_and_save_courses(courses_df):
    courses_df = courses_df[courses_df['CANVAS_NEEDED'] == 'Y']
    selected_columns = ['long_name', 'short_name', 'status', 'course_id', 'account_id', 'term_id', 'blueprint_course_id']
    courses_df = courses_df[selected_columns]
    courses_df.to_csv('temp_outputs/courses.csv', index=False)