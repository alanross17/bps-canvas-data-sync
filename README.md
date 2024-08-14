# Brockton My School to Canvas

A data sync tool to convert MySchool exports to files compatible with Canvas SIS import. Currently this script can only handle enrolment file creation, but future plans to add user management are in progress.

## How to Use

### 1.0 Collect Required Data

This script relies on specific data exports from MySchool to generate enrolment data for Canvas.

#### 1.1 Get Courses CSV File.

1. From MySchool select "Data Reports" -> "Export".
2. Then select the following

    - "Course Info"
    - "Excel 2007-2010 (*.xlsx)"
    - Filter by: "By school level", and select "Middle School"

    Requried Data:

    - "Course Name"
    - "Course ID"
    - "Trax Code"

3. Repeat this process, selecting "Senior School" in the filter settings.
4. Merge these files with a useful name in your working directory. This file will not be read directly by our script, and thus does not need to be anything particular.

#### 1.2 Get Student Enrollment

1. Again, from MySchool select "Data Reports" -> "Export".
2. Then select the following:

    - "Course Info"
    - "Comma Separated Value (*.csv)"
    - Filter by: "By school level", and select "Middle School"

    Requried Data:

    - "Course Name"
    - "Course ID"
    - "Subject"
    - "Student list (per line)"

3. Repeat this process, selecting "Senior School" in the filter settings.
4. Merge these two .csv files and save as `enrollments.csv` in `temp_inputs`
5. Ensure that headings in the file match the following:
`"course_name","course_id","subject","name","","student_id"`

#### 1.3 Get Teacher Enrollemnt

1. Again, from MySchool select "Data Reports" -> "Export".
2. Then select the following:

    - "Course Info"
    - "Comma Separated Value (*.csv)"
    - Filter by: "By school level", and select "Middle School"

    Requried Data:

    - "Course Name"
    - "Course ID"
    - "Subject"
    - "Teacher (split)"

3. Repeat this process, selecting "Senior School" in the filter settings.
4. Merge these two .csv files and save as `teacher_enroll.csv` in `temp_inputs`
5. Ensure that headings in the file match the following:
`course_name,course_id,subject,teacher,...`

#### 1.4 Get Teacher User IDs

1. From MySchool select "Data Reports" -> "Export".
2. Then select the following:

    - "User Info"
    - "Comma Separated Value (*.csv)"
    - Filters: Choose staff and teachers for all school levels.

    Requried Data:

    - "Surname"
    - "Name"
    - "User ID"

3. Save this file as `teacher_ids.csv` in `temp_inputs`.
4. Ensure that headers in the file match the following:
`"SURNAME","NAME","USER ID"`

### 2.0 Prepare the Course Data

Courses in MySchool don't exactly match Canvas requirements. Many courses overlap, some are not required on Canvas at all, and many need different names and coding. Addtionally Canvas template and term information must be added here.

1. Open your initial courses `.xlsx` file in Excel. Change the existing columns to match the following:
`COURSE_LABEL, MS_COURSE_ID, SCHOOL_LEVEL, TRAX`. Then, add the following columns: `MERGE_CODE, CANVAS_NEEDED, TWO_YEAR_FLAG, term_id, blueprint_course_id, name_override, code_override, long_name, short_name, status, course_id, account_id`.
2. Begin filling the merge codes, and Canvas flags as needed.
3. Fill template course codes (TODO: add formulae here)
4. Fill long and short names (TODO: add formulae here)
5. Fill term IDs (TODO: add formulae here)
6. Fill all remaing info for Canvas.
7. Export this file as `courses.csv` to `temp_inputs`.

### 3.0 Run the Script

Navigate to your working directory in terminal and run `python3 enrollments.py`.
