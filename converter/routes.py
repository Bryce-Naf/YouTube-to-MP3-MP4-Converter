import shutil
import uuid
from pathlib import Path

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    url_for,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from converter import db
from converter.media_processing import (
    MediaProcessingError,
    MediaToolsUnavailable,
    MediaValidationError,
    SUPPORTED_INPUT_FORMATS,
    UnsupportedMediaError,
    convert_media,
    probe_media,
)
from converter.models import ConversionJob

api = Blueprint("api", __name__)


@api.get("/")
def index():
    return render_template("index.html")


@api.get("/api/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok")


def remove_job_files(job_directory: Path) -> None:
    try:
        shutil.rmtree(job_directory)
    except FileNotFoundError:
        pass
    except OSError:
        current_app.logger.exception("Unable to remove failed media job files.")


@api.post("/api/convert")
def convert_upload():
    uploaded_file = request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        return jsonify(error="Choose a media file to upload."), 400

    output_format = request.form.get("output_format", "").lower()
    if output_format not in {"mp3", "mp4"}:
        return jsonify(error="Choose MP3 or MP4 as the output format."), 400

    original_filename = secure_filename(uploaded_file.filename)
    extension = Path(original_filename).suffix.lower()
    if extension not in SUPPORTED_INPUT_FORMATS:
        return (
            jsonify(
                error="Supported inputs are MP4, MOV, MKV, WebM, AVI, MP3, WAV, M4A, AAC, FLAC, and OGG."
            ),
            415,
        )

    job_id = uuid.uuid4().hex
    storage_root = Path(current_app.config["MEDIA_STORAGE_PATH"])
    job_directory = storage_root / job_id
    source_path = job_directory / f"source{extension}"
    output_path = job_directory / f"converted.{output_format}"

    try:
        job_directory.mkdir(parents=True, exist_ok=False)
        uploaded_file.save(source_path)
        if source_path.stat().st_size > current_app.config["MAX_UPLOAD_BYTES"]:
            raise MediaValidationError("Upload exceeds the 500 MB file size limit.")

        media_info = probe_media(source_path)
        if output_format == "mp3" and "audio" not in media_info.stream_types:
            raise MediaValidationError("This video does not contain an audio track to convert.")

        convert_media(source_path, output_path, output_format, media_info)
        output_info = probe_media(output_path)
        if output_format == "mp3" and output_info.stream_types != {"audio"}:
            raise MediaProcessingError("The generated MP3 did not pass format validation.")
        if output_format == "mp4" and "video" not in output_info.stream_types:
            raise MediaProcessingError("The generated MP4 did not pass format validation.")

        source_kind = "video" if "video" in media_info.stream_types else "audio"
        job = ConversionJob(
            id=job_id,
            original_filename=original_filename,
            source_extension=extension,
            source_kind=source_kind,
            output_format=output_format,
            duration_seconds=media_info.duration_seconds,
        )
        db.session.add(job)
        db.session.commit()
    except UnsupportedMediaError as error:
        db.session.rollback()
        remove_job_files(job_directory)
        return jsonify(error=str(error)), 415
    except MediaValidationError as error:
        db.session.rollback()
        remove_job_files(job_directory)
        return jsonify(error=str(error)), 422
    except MediaToolsUnavailable as error:
        db.session.rollback()
        remove_job_files(job_directory)
        current_app.logger.error("Media tools unavailable: %s", error)
        return jsonify(error="Media processing is unavailable. Install FFmpeg and FFprobe."), 503
    except MediaProcessingError as error:
        db.session.rollback()
        remove_job_files(job_directory)
        current_app.logger.warning("Media conversion failed: %s", error)
        return (
            jsonify(error="Media conversion failed. Check that the input is valid and try again."),
            422,
        )
    except (OSError, SQLAlchemyError):
        db.session.rollback()
        remove_job_files(job_directory)
        current_app.logger.exception("Unable to store or record media conversion.")
        return jsonify(error="Unable to store or record this conversion."), 500

    return jsonify(
        id=job.id,
        filename=f"{Path(original_filename).stem}.{output_format}",
        download_url=url_for("api.download_conversion", job_id=job.id),
    ), 201


@api.get("/api/download/<job_id>")
def download_conversion(job_id: str) -> Response | tuple[Response, int]:
    job = db.session.get(ConversionJob, job_id)
    if job is None:
        return jsonify(error="Conversion not found."), 404

    output_path = (
        Path(current_app.config["MEDIA_STORAGE_PATH"])
        / job.id
        / f"converted.{job.output_format}"
    )
    if not output_path.is_file():
        return jsonify(error="Converted file is no longer available."), 404

    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"{Path(job.original_filename).stem}.{job.output_format}",
        mimetype="audio/mpeg" if job.output_format == "mp3" else "video/mp4",
    )
