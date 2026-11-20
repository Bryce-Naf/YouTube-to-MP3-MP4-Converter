import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

MAX_MEDIA_DURATION_SECONDS = 2 * 60 * 60
MAX_OUTPUT_BYTES = 1024 * 1024 * 1024
PROBE_TIMEOUT_SECONDS = 60
CONVERSION_TIMEOUT_SECONDS = 30 * 60

SUPPORTED_INPUT_FORMATS = {
    ".mp4": {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"},
    ".mov": {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"},
    ".mkv": {"matroska"},
    ".webm": {"matroska", "webm"},
    ".avi": {"avi"},
    ".mp3": {"mp3"},
    ".wav": {"wav"},
    ".m4a": {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"},
    ".aac": {"aac"},
    ".flac": {"flac"},
    ".ogg": {"ogg"},
}


class UnsupportedMediaError(ValueError):
    pass


class MediaValidationError(ValueError):
    pass


class MediaToolsUnavailable(RuntimeError):
    pass


class MediaProcessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class MediaInfo:
    format_names: frozenset[str]
    stream_types: frozenset[str]
    duration_seconds: float


def probe_media(path: Path) -> MediaInfo:
    extension = path.suffix.lower()
    expected_formats = SUPPORTED_INPUT_FORMATS.get(extension)
    if expected_formats is None:
        raise UnsupportedMediaError("That file type is not supported.")

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=format_name,duration:stream=codec_type,duration",
                "-of",
                "json",
                "-protocol_whitelist",
                "file,crypto,data",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise MediaToolsUnavailable("FFprobe is not installed or is not on PATH.") from error
    except subprocess.TimeoutExpired as error:
        raise MediaValidationError("The uploaded file took too long to inspect.") from error
    except subprocess.CalledProcessError as error:
        raise MediaValidationError("The uploaded file is not valid supported media.") from error

    try:
        probe_result = json.loads(result.stdout)
        format_info = probe_result.get("format", {})
        format_names = frozenset(str(format_info.get("format_name", "")).split(","))
        streams = probe_result.get("streams", [])
        stream_types = frozenset(
            stream.get("codec_type")
            for stream in streams
            if stream.get("codec_type") in {"audio", "video"}
        )
        duration_value = format_info.get("duration")
        if duration_value is None:
            duration_value = max(
                (float(stream["duration"]) for stream in streams if stream.get("duration")),
                default=None,
            )
        duration_seconds = float(duration_value)
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise MediaValidationError("The uploaded file has unreadable media metadata.") from error

    if not format_names.intersection(expected_formats):
        raise MediaValidationError("The file extension does not match its actual media format.")
    if not stream_types:
        raise MediaValidationError("The uploaded file does not contain audio or video.")
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise MediaValidationError("Could not determine a valid media duration.")
    if duration_seconds > MAX_MEDIA_DURATION_SECONDS:
        raise MediaValidationError("Media longer than two hours is not supported.")

    return MediaInfo(format_names, stream_types, duration_seconds)


def convert_media(
    source_path: Path,
    output_path: Path,
    output_format: str,
    media_info: MediaInfo,
) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-y",
        "-v",
        "error",
        "-protocol_whitelist",
        "file,crypto,data,lavfi",
    ]

    if output_format == "mp3":
        if "audio" not in media_info.stream_types:
            raise MediaValidationError("This video does not contain an audio track to convert.")
        command.extend(
            [
                "-i",
                str(source_path),
                "-map",
                "0:a:0",
                "-vn",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
            ]
        )
    elif output_format == "mp4":
        if "video" in media_info.stream_types:
            command.extend(
                [
                    "-i",
                    str(source_path),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0?",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                ]
            )
        else:
            command.extend(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=1280x720:r=30",
                    "-i",
                    str(source_path),
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-shortest",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-tune",
                    "stillimage",
                    "-pix_fmt",
                    "yuv420p",
                ]
            )
        command.extend(["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4"])
    else:
        raise MediaValidationError("Choose MP3 or MP4 as the output format.")

    command.extend(["-fs", str(MAX_OUTPUT_BYTES), str(output_path)])

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise MediaToolsUnavailable("FFmpeg is not installed or is not on PATH.") from error
    except subprocess.TimeoutExpired as error:
        raise MediaProcessingError("Media conversion timed out.") from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or "").strip()[-1000:]
        raise MediaProcessingError(details or "FFmpeg could not convert this media.") from error

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise MediaProcessingError("FFmpeg did not produce a valid output file.")
    if output_path.stat().st_size >= MAX_OUTPUT_BYTES:
        raise MediaProcessingError("The converted file exceeds the one-gigabyte output limit.")
