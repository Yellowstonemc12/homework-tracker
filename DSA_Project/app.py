import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Homework Submission Tracker", page_icon="📘")

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "list" / "HW_LIST.txt"


def load_names():
    if not FILE_PATH.exists():
        FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FILE_PATH.write_text("", encoding="utf-8")
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return f.readlines()


def save_names(names):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(names)


def is_digits_only(text):
    return text.isdigit()


def is_letters_only(text):
    cleaned = text.replace(" ", "").replace("-", "").replace("'", "")
    return cleaned.isalpha()


st.title("Homework Submission Tracker")

# st.write("File location:", FILE_PATH)

names = load_names()

st.subheader("Students who did not submit homework")

if names:
    for name in names:
        st.write(name.strip())
else:
    st.info("No records found yet.")

tab1, tab2 = st.tabs(["Add records", "Remove records"])

with tab1:
    st.subheader("Add students who did not submit")

    with st.form("add_form"):
        hwname = st.text_input("Homework name")
        numofnames = st.text_input("Number of students")

        submitted_names = []
        count_valid = numofnames.isdigit()

        if count_valid and int(numofnames) > 0:
            for i in range(int(numofnames)):
                submitted_names.append(
                    st.text_input(f"Enter student's name #{i+1}")
                )

        add_submit = st.form_submit_button("Save records")

        if add_submit:
            if not hwname.strip():
                st.error("Please enter the homework name.")
            elif not is_digits_only(numofnames):
                st.error("Number of students must be digits only.")
            else:
                num = int(numofnames)
                if num <= 0:
                    st.error("Number of students must be at least 1.")
                elif len(submitted_names) != num:
                    st.error("Please fill in all student name fields.")
                else:
                    invalid_names = [
                        n for n in submitted_names
                        if not n.strip() or not is_letters_only(n.strip())
                    ]

                    if invalid_names:
                        st.error("Student names must contain letters only.")
                    else:
                        updated_names = load_names()

                        existing_records = {
                            line.strip().lower() for line in updated_names
                        }

                        added_records = []
                        skipped_records = []

                        for student_name in submitted_names:
                            record = f"{hwname.strip()}: {student_name.strip()}"
                            record_key = record.lower()

                            if record_key in existing_records:
                                skipped_records.append(record)
                            else:
                                updated_names.append(record + "\n")
                                existing_records.add(record_key)
                                added_records.append(record)

                        save_names(updated_names)

                        if added_records:
                            st.success(f"{len(added_records)} record(s) added successfully.")

                        if skipped_records:
                            st.warning(
                                "These duplicate record(s) were skipped:\n\n- "
                                + "\n- ".join(skipped_records)
                            )

                        if added_records:
                            st.rerun()

with tab2:
    st.subheader("Remove existing records")

    current_names = load_names()

    if current_names:
        options = [line.strip() for line in current_names]

        selected_records = st.multiselect(
            "Select record(s) to remove",
            options
        )

        if st.button("Remove selected record(s)"):
            if not selected_records:
                st.error("Please select at least one record to remove.")
            else:
                updated_names = [
                    line for line in current_names
                    if line.strip() not in selected_records
                ]
                save_names(updated_names)
                st.success("Selected record(s) removed successfully.")
                st.rerun()
    else:
        st.info("No records available to remove.")