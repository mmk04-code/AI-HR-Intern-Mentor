"""
Helper script to generate sample requirement documents and submission ZIP archives.
"""

import os
import zipfile
import docx

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_docx_requirements():
    doc = docx.Document()
    doc.add_heading("Company Task Requirements: Full-Stack Task Tracker Module 1", level=1)
    doc.add_paragraph("Build a modular Full-Stack Task Tracker application for managing intern assignments.")

    doc.add_heading("Mandatory Specifications", level=2)
    doc.add_paragraph("1. Database Schema & Models: Implement persistent models for User, Project, and TaskItem with foreign keys.")
    doc.add_paragraph("2. Core API / Business Logic: Create task creation, listing, updating, and validation on task titles.")
    doc.add_paragraph("3. User Interface & Interaction: Provide an interactive dashboard displaying active tasks with filters.")
    doc.add_paragraph("4. Error Handling & Resilience: Gracefully handle database disconnections and missing records.")
    doc.add_paragraph("5. Documentation & Tests: Comprehensive README.md and unit test cases.")

    out_path = os.path.join(SAMPLE_DIR, "company_requirements.docx")
    doc.save(out_path)
    print(f"Generated {out_path}")


def create_txt_requirements():
    md_path = os.path.join(SAMPLE_DIR, "company_requirements.md")
    txt_path = os.path.join(SAMPLE_DIR, "company_requirements.txt")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {txt_path}")


def create_sample_zip_v1():
    """Revision 1: Partial implementation (missing tests, validation, and error handling)"""
    zip_path = os.path.join(SAMPLE_DIR, "candidate_submission_v1_partial.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("README.md", """# Task Tracker - Intern Submission (Revision 1)
Author: Aarav Sharma
This is the preliminary submission for Module 1.

Implemented:
- Basic database schema in models.py
- Basic task routes in app.py
""")
        zf.writestr("models.py", """import sqlite3

def init_models():
    conn = sqlite3.connect("tasks.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS TaskItem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        status TEXT,
        project_id INTEGER
    )''')
    conn.commit()
    conn.close()
""")
        zf.writestr("app.py", """from flask import Flask, request, jsonify
from models import init_models

app = Flask(__name__)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    return jsonify({"tasks": []})

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    # Title validation not yet added
    return jsonify({"message": "Task created", "data": data})

if __name__ == '__main__':
    init_models()
    app.run(port=5000)
""")
    print(f"Generated {zip_path}")


def create_sample_zip_v2():
    """Revision 2: Completed implementation with validation, tests, and error handling"""
    zip_path = os.path.join(SAMPLE_DIR, "candidate_submission_v2_completed.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("README.md", """# Task Tracker - Intern Submission (Revision 2 - Completed)
Author: Aarav Sharma
Complete implementation addressing all Module 1 review feedback.

Features:
- Full User, Project, TaskItem database models with audit timestamps.
- Validation: minimum 5 character title check.
- Status filters and interactive dashboard interface.
- Complete error handling (404 and DB disconnect resilience).
- Unit tests in test_tasks.py.
""")
        zf.writestr("models.py", """import sqlite3

def init_models():
    conn = sqlite3.connect("tasks.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Project (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS TaskItem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES Project(id),
        user_id INTEGER REFERENCES User(id),
        title TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        priority TEXT DEFAULT 'normal',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
""")
        zf.writestr("app.py", """from flask import Flask, request, jsonify
import sqlite3
from models import init_models

app = Flask(__name__)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    status = request.args.get('status')
    priority = request.args.get('priority')
    # Filter implementation
    return jsonify({"tasks": [], "filters": {"status": status, "priority": priority}})

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json(silent=True)
    if not data or not data.get('title'):
        return jsonify({"error": "Task title is required"}), 400
    if len(data['title'].strip()) < 5:
        return jsonify({"error": "Task title must be at least 5 characters"}), 422
    return jsonify({"message": "Task successfully created", "item": data}), 201

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

if __name__ == '__main__':
    init_models()
    app.run(port=5000)
""")
        zf.writestr("test_tasks.py", """import unittest
from app import app

class TaskTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_validation_short_title(self):
        resp = self.client.post('/tasks', json={'title': 'hi'})
        self.assertEqual(resp.status_code, 422)

    def test_valid_task_creation(self):
        resp = self.client.post('/tasks', json={'title': 'Valid Task Title'})
        self.assertEqual(resp.status_code, 201)

if __name__ == '__main__':
    unittest.main()
""")
    print(f"Generated {zip_path}")


if __name__ == "__main__":
    create_docx_requirements()
    create_txt_requirements()
    create_sample_zip_v1()
    create_sample_zip_v2()
