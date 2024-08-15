import pandas as pd
from file_handling import load_and_combine_csv, load_csv

def melt_teachers(df):
    df.dropna(axis=1, how='all', inplace=True)
    teacher_columns = df.columns[df.columns.get_loc("teacher"):]
    melted_df = df.melt(id_vars=["course_name", "course_id", "subject"], value_vars=teacher_columns, var_name="Teacher Role", value_name="name")
    melted_df = melted_df.dropna(subset=["name"])
    return melted_df[["course_name", "course_id", "subject", "name"]]

def map_teacher_ids(teacher_df, id_df):
    id_df['fullname'] = id_df['SURNAME'] + ', ' + id_df['NAME']
    id_map = id_df.set_index('fullname')['USER ID'].to_dict()
    teacher_df['user_id'] = teacher_df['name'].map(id_map)
    teacher_df['user_id'] = teacher_df['user_id'].apply(lambda x: str(int(x)) if pd.notna(x) else x)
    return teacher_df

def preprocess_teacher_enrollments(file_path):
    df = load_and_combine_csv(file_path)
    formatted_df = melt_teachers(df)
    teacher_ids_df = load_csv('temp_inputs/teacher_ids.csv')
    mapped_df = map_teacher_ids(formatted_df, teacher_ids_df)
    mapped_df['user_id'] = mapped_df['user_id'].astype(str)
    mapped_df['course_id'] = mapped_df['course_id'].astype(str)
    mapped_df['role'] = 'teacher'
    return mapped_df