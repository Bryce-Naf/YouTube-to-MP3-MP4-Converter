# YouTube-to-MP3-MP4-Converter

A Flask application for previewing YouTube videos and converting audio or video
files uploaded from your computer. The YouTube URL field uses YouTube's
privacy-enhanced embedded player; it does not download the YouTube video.
Upload and convert only media you own or are authorized to use.

## Features

- Preview supported YouTube watch, Shorts, embed, and `youtu.be` URLs in the
  homepage.
- Upload audio or video and convert it to MP3 or MP4.
- Download completed conversions from the homepage.
- Check service and database availability at `/api/health`.

### Supported uploads and conversion limits

Accepted input extensions are MP4, MOV, MKV, WebM, AVI, MP3, WAV, M4A, AAC,
FLAC, and OGG. FFprobe checks the actual container, audio/video streams, and
duration; the filename extension alone is not trusted.

- Maximum upload size: 500 MB.
- Maximum source duration: 2 hours.
- Maximum converted output size: 1 GB.
- MP3 conversion requires an audio track.
- Video-to-MP4 conversion creates an H.264/AAC MP4.
- Audio-only-to-MP4 conversion creates a 1280x720 black background with AAC
  audio.

The upload and conversion request is synchronous and may take up to 30 minutes.

## API

- `GET /api/health` checks the database and returns a JSON status.
- `POST /api/convert` accepts multipart form fields `file` and
  `output_format` (`mp3` or `mp4`). On success it returns a job ID, output
  filename, and download URL.
- `GET /api/download/<job_id>` downloads a completed conversion.

Upload and conversion errors are returned as JSON with an appropriate HTTP
error status.

## Storage and limitations

Uploaded originals and converted files are stored under
`instance/media_jobs/<job_id>`. SQLite stores conversion metadata. The database
defaults to `instance/app.sqlite`; set `DATABASE_URL` to use a different
database.

Files are retained until manually removed; automatic expiration and user
authentication are not implemented. Cloud Run's local filesystem and SQLite
data are ephemeral and local to an instance. A production deployment that needs
persistent files or multiple instances should use managed storage and a managed
database, and should add authentication, request controls, and a retention
policy.

## Technology stack

- Frontend: HTML, CSS, and JavaScript served by Flask
- Backend: Python, Flask, and REST API
- Database: SQLite and Flask-SQLAlchemy
- Media inspection and conversion: FFprobe and FFmpeg
- Deployment: Docker, Google Cloud Run, and GitHub Actions
- Development/AI assistance: GitHub Copilot

## Run locally

Requires Python 3.12 or newer and FFmpeg/FFprobe available on `PATH`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app wsgi run --debug
```

Open `http://127.0.0.1:5000`. FFmpeg and FFprobe can be checked with:

```powershell
ffmpeg -version
ffprobe -version
```

Run the tests with:

```powershell
python -m pytest
```

## Run with Docker

The Docker image installs FFmpeg and FFprobe.

```powershell
docker build -t media-converter .
docker run --rm -p 8080:8080 media-converter
```

Open `http://localhost:8080`. The health endpoint is at
`http://localhost:8080/api/health`. With `--rm`, the container and its local
uploads are removed when it stops.

## Deploy to Google Cloud Run

The GitHub Actions workflow deploys on pushes to `main`. Configure these GitHub
Actions secrets:

- `GCP_SA_KEY`: the full service-account JSON key.
- `GCP_PROJECT_ID`: the Google Cloud project ID.
- `GCP_REGION`: the Cloud Run region, such as `us-central1`.

The service account needs permission to build and deploy to Cloud Run. The
workflow uses a long-lived JSON key; restrict its permissions, keep it in
GitHub Secrets, and rotate it if exposed. Workload Identity Federation is
preferable when available.

The workflow tests the application, then deploys one service named
`youtube-media-converter`. The frontend is served by Flask in the same
container as the backend. After a successful deployment, find the URL in the
GitHub Actions deploy logs or in Google Cloud Console under Cloud Run >
Services.

## AI Usage

Copilot assisted in the creation of this entire program. It helped in figuring
out issues related to copyright and how the program could be made despite
having these issues.
