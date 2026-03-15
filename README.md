# Yield Monitor Web Application

A FastAPI-based yield monitoring dashboard built for the practical exam.

## Stack
- Python
- FastAPI
- SQLite
- SQLAlchemy
- HTML / CSS / JavaScript
- Chart.js
- Selenium

## Features
- `POST /tests` to insert a manual test record
- `GET /tests` to list all records
- `GET /stats` to return per-part yield statistics
- `GET /daily` to return last 7 days of testing counts
- Single-page dashboard with:
  - Daily bar chart
  - Part distribution pie chart
  - Yield gauge
- Manual Testing modal form
- View API button for `/docs`
- View Script button for the Selenium script

## Project Files
- `main.py` — FastAPI app entry point
- `database.py` — SQLite connection and ORM model
- `templates/index.html` — dashboard UI
- `static/style.css` — dashboard styling
- `static/app.js` — frontend logic
- `test_yield.py` — Selenium automation script
- `requirements.txt` — dependencies

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
# On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open:
- Dashboard: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## Run Selenium Test
1. Make sure the app is already running on `http://localhost:8000`
2. Make sure Chrome and ChromeDriver are available
3. Run:
```bash
python test_yield.py
```

## Deployment
You can deploy this on Replit, Render, Railway, or PythonAnywhere.

Example start command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Notes
- The database file is created automatically as `yield_monitor.db`
- The timestamp is generated on insert
- The gauge changes color based on yield:
  - Green >= 90%
  - Yellow >= 80%
  - Red < 80%
