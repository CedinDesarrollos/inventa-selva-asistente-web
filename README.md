# Selva Web (Flask)

## Requisitos
- Python 3.10+
- pip

## Setup
```bash
cp .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
export FLASK_APP=app.py
flask run
