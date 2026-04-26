import streamlit as st
from pathlib import Path
import csv
from datetime import datetime

st.set_page_config(page_title="Homework Submission Tracker", page_icon="📘")

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "list" / "HW_LIST.csv"

HEADERS = ["Date", "Level", "Subject", "Homework", "Student"]


def ensure_file_exists():
    FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FILE_PATH.exists():
        with open(FILE_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)


def load_records():
    ensure_file_exists()
    with open(FILE_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_records(records):
    with open(FILE_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(records)


def is_letters_only(text):
    cleaned = text.replace(" ", "").replace("-", "").replace("'", "")
    return cleaned.isalpha()


st.title("Homework Submission Tracker")

records = load_records()

tab1, tab2 = st.tabs(["View Records", "Add / Remove Records"])

with tab1:
    st.subheader("Find Records")

    if records:
        levels = sorted(set(r["Level"] for r in records if r["Level"]))
        subjects = sorted(set(r["Subject"] for r in records if r["Subject"]))
        homework_list = sorted(set(r["Homework"] for r in records if r["Homework"]))

        selected_level = "All"
        selected_subject = "All"
        selected_homework = "All"
        student_search = ""

        with st.expander("🔎 Filters"):
            selected_level = st.selectbox("Filter by Level", ["All"] + levels)
            selected_subject = st.selectbox("Filter by Subject", ["All"] + subjects)
            selected_homework = st.selectbox("Filter by Homework", ["All"] + homework_list)
            student_search = st.text_input("Search student name")

        filtered = records

        if selected_level != "All":
            filtered = [r for r in filtered if r["Level"] == selected_level]

        if selected_subject != "All":
            filtered = [r for r in filtered if r["Subject"] == selected_subject]

        if selected_homework != "All":
            filtered = [r for r in filtered if r["Homework"] == selected_homework]

        if student_search.strip():
            filtered = [
                r for r in filtered
                if student_search.lower() in r["Student"].lower()
            ]

        st.write(f"Showing {len(filtered)} record(s)")

        grouped = {}

        for r in filtered:
            key = f"{r['Level']} | {r['Subject']} | {r['Homework']}"
            grouped.setdefault(key, []).append(r)

        # Sort groups by oldest date first
        sorted_groups = sorted(
            grouped.items(),
            key=lambda x: (
                int(x[0].split("|")[5].strip().replace("Primary ", "")),  # Level
                x[1][0]["Date"]  # Oldest date first
            )
        )
        
        col1, col2 = st.columns(2)
        
        for i, (group, items) in enumerate(sorted_groups):
            target_col = col1 if i % 2 == 0 else col2
        
            # Sort students inside each group by oldest date first
            items = sorted(items, key=lambda x: x["Date"])
        
            with target_col:
                with st.expander(group, expanded=True):
                    for item in items:
                        st.write(f"- {item['Student']}  |  Added on: {item['Date']}")

    else:
        st.info("No records found yet.")

with tab2:
    st.subheader("Add Records")
    if "success_message" in st.session_state:
        st.success(st.session_state["success_message"])
        del st.session_state["success_message"]

    level = st.selectbox(
    "Primary Level",
    ["Primary 1", "Primary 2", "Primary 3", "Primary 4", "Primary 5", "Primary 6"]
    )
    
    subject = st.selectbox(
        "Subject",
        ["English", "Chinese", "Math", "Science", "Higher Chinese", "Others"]
    )
    
    homework = st.text_input("Homework name")
    num_students = st.number_input("Number of students", min_value=1, step=1)
    
    student_names = []
    
    with st.form("add_form"):
        for i in range(num_students):
            student_names.append(st.text_input(f"Student name #{i + 1}"))
    
        submitted = st.form_submit_button("Save Records")

        if submitted:
            if not homework.strip():
                st.error("Please enter the homework name.")
            elif num_students < 1:
                st.error("Number of students must be at least 1.")
            else:
                invalid_names = [
                    name for name in student_names
                    if not name.strip() or not is_letters_only(name.strip())
                ]

                if invalid_names:
                    st.error("Student names must contain letters only.")
                else:
                    current_records = load_records()

                    existing_keys = {
                        (
                            r["Level"].lower(),
                            r["Subject"].lower(),
                            r["Homework"].lower(),
                            r["Student"].lower()
                        )
                        for r in current_records
                    }

                    added = 0
                    skipped = []

                    for student in student_names:
                        new_key = (
                            level.lower(),
                            subject.lower(),
                            homework.strip().lower(),
                            student.strip().lower()
                        )

                        if new_key in existing_keys:
                            skipped.append(student.strip())
                        else:
                            current_records.append({
                                "Date": datetime.now().strftime("%A, %d %B %Y"),
                                "Level": level,
                                "Subject": subject,
                                "Homework": homework.strip(),
                                "Student": student.strip()
                            })
                            existing_keys.add(new_key)
                            added += 1

                    save_records(current_records)

                    if added:
                        st.session_state["success_message"] = f"{added} record(s) added successfully."

                    if skipped:
                        st.warning(
                            "Duplicate record(s) skipped: " + ", ".join(skipped)
                        )

                    st.rerun()

    st.divider()

    st.subheader("Remove Records")

    records = load_records()

    if records:
        options = [
            f"{r['Level']} | {r['Subject']} | {r['Homework']} | {r['Student']} | {r['Date']}"
            for r in records
        ]

        selected = st.multiselect("Select record(s) to remove", options)

        if st.button("Remove Selected Record(s)"):
            updated_records = []

            for r in records:
                label = f"{r['Level']} | {r['Subject']} | {r['Homework']} | {r['Student']} | {r['Date']}"
                if label not in selected:
                    updated_records.append(r)

            save_records(updated_records)
            st.success("Selected record(s) removed.")
            st.rerun()
    else:
        st.info("No records available to remove.")
