from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import csv
from datetime import datetime

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
        f"""
        <tr>
            <td>{r['Date']}</td>
            <td>{r['Level']}</td>
            <td>{r['Subject']}</td>
            <td>{r['Homework']}</td>
            <td>{r['Student']}</td>
        </tr>
        """
        for r in records
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Homework Tracker</title>

        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }}

            body {{
                background: #f4f7fb;
                color: #222;
                padding: 40px;
            }}

            .container {{
                max-width: 1100px;
                margin: auto;
            }}

            .title {{
                font-size: 42px;
                font-weight: bold;
                margin-bottom: 10px;
            }}

            .subtitle {{
                color: #666;
                margin-bottom: 35px;
            }}

            .card {{
                background: white;
                padding: 25px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-bottom: 30px;
            }}

            .card h2 {{
                margin-bottom: 20px;
            }}

            form {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}

            input {{
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 10px;
                font-size: 15px;
            }}

            button {{
                grid-column: span 2;
                padding: 14px;
                border: none;
                border-radius: 12px;
                background: #2563eb;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: 0.2s;
            }}

            button:hover {{
                background: #1d4ed8;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                overflow: hidden;
                border-radius: 12px;
            }}

            th {{
                background: #2563eb;
                color: white;
                padding: 14px;
                text-align: left;
            }}

            td {{
                padding: 14px;
                border-bottom: 1px solid #eee;
            }}

            tr:hover {{
                background: #f9fbff;
            }}

            .empty {{
                text-align: center;
                color: #777;
                padding: 30px;
            }}

            @media (max-width: 700px) {{
                form {{
                    grid-template-columns: 1fr;
                }}

                button {{
                    grid-column: span 1;
                }}

                .title {{
                    font-size: 32px;
                }}

                table {{
                    font-size: 14px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <div class="title">📘 Homework Tracker</div>
            <div class="subtitle">
                Manage student homework submissions easily
            </div>

            <div class="card">
                <h2>Add Record</h2>

                <form action="/add" method="post">
                    <input name="level" placeholder="Primary Level" required>
                    <input name="subject" placeholder="Subject" required>
                    <input name="homework" placeholder="Homework Name" required>
                    <input name="student" placeholder="Student Name" required>

                    <button type="submit">
                        Add Record
                    </button>
                </form>
            </div>

            <div class="card">
                <h2>📋 Records ({len(records)})</h2>

                {
                    f'''
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Level</th>
                            <th>Subject</th>
                            <th>Homework</th>
                            <th>Student</th>
                        </tr>

                        {rows}
                    </table>
                    '''
                    if records else
                    '<div class="empty">No records yet 🌱</div>'
                }
            </div>

        </div>
    </body>
    </html>
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
