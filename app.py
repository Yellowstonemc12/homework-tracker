from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import csv
from datetime import datetime

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "list" / "HW_LIST.csv"

HEADERS = ["Date", "Level", "Subject", "Homework", "Student"]


def ensure_file():
    FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FILE_PATH.exists():
        with open(FILE_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADERS)


def load_records():
    ensure_file()
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_records(records):
    ensure_file()
    with open(FILE_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(records)


@app.get("/", response_class=HTMLResponse)
def home():
    records = load_records()

    rows = "".join(
        f"<tr><td>{r['Date']}</td><td>{r['Level']}</td><td>{r['Subject']}</td>"
        f"<td>{r['Homework']}</td><td>{r['Student']}</td></tr>"
        for r in records
    )

    return f"""
    <html>
    <head>
        <title>Homework Tracker</title>
    </head>
    <body>
        <h1>📘 Homework Submission Tracker</h1>

        <h2>Add Record</h2>
        <form action="/add" method="post">
            Level: <input name="level"><br>
            Subject: <input name="subject"><br>
            Homework: <input name="homework"><br>
            Student: <input name="student"><br>
            <button type="submit">Add</button>
        </form>

        <h2>Records</h2>
        <table border="1">
            <tr>
                <th>Date</th><th>Level</th><th>Subject</th><th>Homework</th><th>Student</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """


@app.post("/add")
def add_record(
    level: str = Form(...),
    subject: str = Form(...),
    homework: str = Form(...),
    student: str = Form(...)
):
    records = load_records()

    records.append({
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Level": level,
        "Subject": subject,
        "Homework": homework,
        "Student": student
    })

    save_records(records)
    return RedirectResponse("/", status_code=303)
