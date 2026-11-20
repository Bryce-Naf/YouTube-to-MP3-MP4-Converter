# YouTube-to-MP3-MP4-Converter

A starter web application for media conversion. The initial scaffold includes a
Flask application, a basic HTML/CSS/JavaScript interface, a health-check REST
endpoint, and SQLite configuration through Flask-SQLAlchemy.

The conversion engine is intentionally not implemented yet. Future functionality
should only process media the user owns or is authorized to use.

## Technology stack

- Frontend: HTML, CSS, and JavaScript
- Backend: Python, Flask, and REST API
- Database: SQLite and Flask-SQLAlchemy
- Deployment: Docker, Google Cloud Run, and GitHub Actions
- Development/AI assistance: GitHub Copilot

## Run locally

Requires Python 3.12 or newer.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app wsgi run --debug
```

Open `http://127.0.0.1:5000`. The API health check is available at
`http://127.0.0.1:5000/api/health`.

Run the tests with:

```powershell
python -m pytest
```

## Run with Docker

```powershell
docker build -t media-converter .
docker run --rm -p 8080:8080 media-converter
```

## Deploy to Google Cloud Run

The GitHub Actions workflow deploys on pushes to `main`. Configure these GitHub
Actions repository variables before enabling it:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `GCP_PROJECT_ID`
- `GCP_REGION`

The Google Cloud service account must be configured for Workload Identity
Federation and have the permissions needed to build and deploy to Cloud Run.

SQLite storage in Cloud Run is ephemeral and local to an instance. A production
deployment that needs persistent data or multiple instances should use a
managed database.
