# YouTube-to-MP3-MP4-Converter

A Flask web application for previewing YouTube videos with YouTube's embedded
player and converting media files uploaded by the user. Uploaded media should
only be files the user owns or is authorized to use.

## Technology stack

- Frontend: HTML, CSS, and JavaScript
- Backend: Python, Flask, and REST API
- Database: SQLite and Flask-SQLAlchemy
- Deployment: Docker, Google Cloud Run, and GitHub Actions
- Development/AI assistance: GitHub Copilot

## Upload and convert media

The homepage accepts local audio and video uploads and offers MP3 or MP4 output.
Supported inputs are MP4, MOV, MKV, WebM, AVI, MP3, WAV, M4A, AAC, FLAC, and OGG.
FFprobe verifies the actual media container, streams, and duration; a file's
extension alone is not considered sufficient validation. MP3 output requires an
audio track. Audio-only files converted to MP4 receive a black video background.

Uploads are limited to 500 MB and two hours of media. Converted output is limited
to 1 GB. FFmpeg and FFprobe must be installed and available on `PATH` when running
outside Docker. Uploaded sources, converted files, and job metadata are stored
locally under `instance/media_jobs` and in the SQLite database, respectively.
Files are currently retained until manually removed.

## Run locally

Requires Python 3.12 or newer, plus FFmpeg/FFprobe on `PATH`. The Docker image
installs FFmpeg automatically.

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

The GitHub Actions workflow deploys on pushes to `main`. Add the service
account's JSON key as the GitHub Actions secret `GCP_SA_KEY`. Configure these
repository variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`

The service account must have the permissions needed to build and deploy to
Cloud Run. A JSON key is a long-lived credential; restrict its permissions and
rotate it if exposed. Workload Identity Federation is preferable when available.

The current frontend is served by Flask, so one Cloud Run service hosts both
frontend and backend.

Uploaded files and SQLite storage in Cloud Run are ephemeral and local to an
instance. A production deployment that needs persistent files or multiple
instances should use managed storage and a managed database.

## AI Usage

Copilot assisted in the creation of this entire program. It helped in figuring out issues related to copyright and how the program could be made despite having these issues. 