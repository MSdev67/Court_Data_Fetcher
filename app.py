import os
import sqlite3
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

DATABASE = 'court_data.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT NOT NULL,
            case_number TEXT NOT NULL,
            filing_year TEXT NOT NULL,
            query_time TEXT NOT NULL,
            raw_response TEXT,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

def get_case_data_mock(case_type, case_number, filing_year):
    print(f"Simulating fetch for: {case_type}-{case_number}-{filing_year}")
    time.sleep(1.5)

    if case_number == "1234":
        mock_data = {
            "case_title": "Sharma Enterprises vs Delhi Municipal Corporation",
            "court": "Delhi High Court",
            "judge": "Hon'ble Justice A. Kumar",
            "filing_date": "15-03-2023",
            "next_hearing_date": "10-12-2023",
            "status": "Pending",
            "orders": [
                {
                    "date": "05-11-2023",
                    "type": "Interim Order",
                    "description": "Respondent directed to file reply within 4 weeks",
                    "pdf_link": f"/download_pdf?case_id={case_type}-{case_number}-{filing_year}-order1",
                    "pdf_size": "45KB"
                }
            ],
            "overall_status": "success",
            "raw_html_snippet": "<html><body>Simulated HTML content</body></html>"
        }
    elif case_number == "5678":
        mock_data = {
            "case_title": "Verma & Sons vs State of NCT Delhi",
            "court": "Delhi High Court",
            "judge": "Hon'ble Justice P. Singh",
            "filing_date": "01-06-2022",
            "next_hearing_date": "N/A",
            "status": "Disposed",
            "orders": [
                {
                    "date": "25-01-2024",
                    "type": "Final Judgment",
                    "description": "Petition dismissed.",
                    "pdf_link": f"/download_pdf?case_id={case_type}-{case_number}-{filing_year}-judgment1",
                    "pdf_size": "120KB"
                }
            ],
            "overall_status": "success",
            "raw_html_snippet": "<html><body>Simulated HTML content</body></html>"
        }
    elif case_number == "999":
        mock_data = {
            "overall_status": "error",
            "message": "Case not found or invalid input."
        }
    else:
        mock_data = {
            "case_title": f"Generic Case {case_number} vs Others",
            "court": "Delhi High Court",
            "judge": "Hon'ble Justice J. Doe",
            "filing_date": "01-01-2023",
            "next_hearing_date": "N/A",
            "status": "Active",
            "orders": [
                {
                    "date": "01-07-2024",
                    "type": "Status Report",
                    "description": "Status report filed by parties.",
                    "pdf_link": f"/download_pdf?case_id={case_type}-{case_number}-{filing_year}-order1",
                    "pdf_size": "20KB"
                }
            ],
            "overall_status": "success",
            "raw_html_snippet": f"<html><body>Simulated HTML content</body></html>"
        }

    return mock_data

def get_ai_response(prompt, context_case_data=None):
    messages = []
    
    if context_case_data:
        case_context_str = f"Case: {context_case_data.get('case_title', 'N/A')}, Number: {context_case_data.get('case_number_full', 'N/A')}, Status: {context_case_data.get('case_status', 'N/A')}"
        messages.append({"role": "system", "content": f"You are a legal assistant. Context: {case_context_str}"})
    else:
        messages.append({"role": "system", "content": "You are a legal assistant. Answer legal questions."})

    messages.append({"role": "user", "content": prompt})

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return "Error: OpenAI API key not configured."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI API error: {e}")
        return "I'm currently unable to connect to the AI service."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_case', methods=['POST'])
def fetch_case():
    case_type = request.form.get('caseType')
    case_number = request.form.get('caseNumber')
    filing_year = request.form.get('filingYear')

    if not all([case_type, case_number, filing_year]):
        return jsonify({"status": "error", "message": "All fields are required."}), 400

    query_time = datetime.now().isoformat()
    raw_response_data = {}
    db_log_status = "failed"

    try:
        data = get_case_data_mock(case_type, case_number, filing_year)
        raw_response_data = data.get("raw_html_snippet", "No raw HTML available")
        response_status = data.get("overall_status", "error")

        if response_status == "success":
            db_log_status = "success"
            return jsonify({
                "status": "success",
                "case_title": data["case_title"],
                "court": data["court"],
                "judge": data["judge"],
                "case_number_full": f"{case_type}/{case_number}/{filing_year}",
                "filing_date": data["filing_date"],
                "next_hearing_date": data["next_hearing_date"],
                "case_status": data["status"],
                "latest_order": data["orders"][0] if data["orders"] else None,
                "fetched_on": datetime.now().strftime("%d-%m-%Y %H:%M IST")
            })
        else:
            db_log_status = "error"
            return jsonify({
                "status": "error",
                "message": data.get("message", "An error occurred")
            }), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO queries (case_type, case_number, filing_year, query_time, raw_response, status) VALUES (?, ?, ?, ?, ?, ?)",
                (case_type, case_number, filing_year, query_time, json.dumps(raw_response_data), db_log_status)
            )
            conn.commit()
            conn.close()
        except Exception as db_error:
            print(f"Database error: {db_error}")

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    user_question = data.get('question')
    case_context = data.get('case_context')

    if not user_question:
        return jsonify({"status": "error", "message": "No question provided"}), 400

    try:
        ai_response = get_ai_response(user_question, case_context)
        return jsonify({"status": "success", "response": ai_response})
    except Exception as e:
        print(f"AI error: {e}")
        return jsonify({"status": "error", "message": "AI service error"}), 500

@app.route('/download_pdf')
def download_pdf():
    case_id = request.args.get('case_id')
    if not case_id:
        return "PDF not found.", 404

    response_content = f"Simulated PDF for case {case_id}"
    return app.response_class(
        response_content,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{case_id}.pdf"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)