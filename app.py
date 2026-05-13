from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import csv
from datetime import datetime

{
  "builds": [
    { "src": "api/app.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "api/app.py" }
  ]
}

app = FastAPI()

FILE_PATH = "/tmp/HW_LIST.csv"  # 🔥 IMPORTANT: use /tmp on Vercel
HEADERS = ["Date", "Level", "Subject", "Homework", "Student"]


def ensure_file():
    if not os.path.exists(FILE_PATH):
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
    <h1>📘 Homework Tracker</h1>

    <form action="/add" method="post">
        Level: <input name="level"><br>
        Subject: <input name="subject"><br>
        Homework: <input name="homework"><br>
        Student: <input name="student"><br>
        <button>Add</button>
    </form>

    <table border="1">
        <tr><th>Date</th><th>Level</th><th>Subject</th><th>Homework</th><th>Student</th></tr>
        {rows}
    </table>
    """


@app.post("/add")
def add(
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
