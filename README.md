# Court_Data_Fetcher
Court-Data Fetcher & Mini-Dashboard (Delhi High Court Simulation)
Core Functionality

Search simulated Delhi High Court cases by:

Case Type (dropdown)

Case Number (input)

Filing Year (input)

Displays case metadata and simulated PDF links

Technical Stack

Frontend: HTML + Tailwind CSS

Backend: Flask (Python)

Database: SQLite (logs all queries)

Key Features
✔ Dynamic results display
✔ Database logging (queries + timestamps)
✔ Simulated PDF downloads
✔ Error handling for invalid inputs

How to Run (macOS/VS Code)

1.python3 -m venv .venv

2.source .venv/bin/activate

3.pip install -r requirements.txt

4.python app.py

Visit http://127.0.0.1:5000

Testing Notes

Normal case: Use Case Number 12345

Error case: Use Case Number 999

Limitations
⚠ Live scraping not implemented (simulated data only)
⚠ No CAPTCHA/anti-bot handling
⚠ SQLite for local development only

For production use, you would need to:

Implement actual scraping with Selenium/Playwright

Add CAPTCHA solving

Migrate to PostgreSQL

The current version demonstrates the full-stack architecture without live website interaction.
