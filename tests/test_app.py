import io

from converter import create_app
from converter.media_processing import MediaInfo


def test_home_page():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b'<label for="media-url">YouTube URL</label>' in response.data
    assert b'id="media-url"' in response.data
    assert b'type="url"' in response.data
    assert b'<button type="submit">Submit URL</button>' in response.data
    assert b'id="video-preview"' in response.data
    assert b'youtube-player' in response.data
    assert b'id="upload-form"' in response.data
    assert b'name="output_format"' in response.data


def test_health_endpoint_checks_database():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_upload_conversion_stores_and_downloads_file(tmp_path, monkeypatch):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "MEDIA_STORAGE_PATH": str(tmp_path / "jobs"),
        }
    )

    def fake_probe(path):
        if path.suffix == ".mp3":
            return MediaInfo(frozenset({"mp3"}), frozenset({"audio"}), 3.0)
        return MediaInfo(frozenset({"mp4"}), frozenset({"audio", "video"}), 3.0)

    def fake_convert(source_path, output_path, output_format, media_info):
        assert source_path.suffix == ".mp4"
        assert output_format == "mp3"
        assert "audio" in media_info.stream_types
        output_path.write_bytes(b"converted media")

    monkeypatch.setattr("converter.routes.probe_media", fake_probe)
    monkeypatch.setattr("converter.routes.convert_media", fake_convert)

    response = app.test_client().post(
        "/api/convert",
        data={
            "file": (io.BytesIO(b"source media"), "my-video.mp4"),
            "output_format": "mp3",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    result = response.get_json()
    job_directory = tmp_path / "jobs" / result["id"]
    assert (job_directory / "source.mp4").read_bytes() == b"source media"
    assert (job_directory / "converted.mp3").read_bytes() == b"converted media"

    download = app.test_client().get(result["download_url"])
    assert download.status_code == 200
    assert download.data == b"converted media"


def test_upload_rejects_unsupported_extension():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})

    response = app.test_client().post(
        "/api/convert",
        data={
            "file": (io.BytesIO(b"not media"), "document.exe"),
            "output_format": "mp3",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert "Supported inputs" in response.get_json()["error"]


def test_upload_enforces_file_size_limit(tmp_path, monkeypatch):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "MEDIA_STORAGE_PATH": str(tmp_path / "jobs"),
            "MAX_UPLOAD_BYTES": 4,
        }
    )
    def fail_probe(path):
        assert path.suffix == ".wav"
        raise AssertionError("oversized file was probed")

    monkeypatch.setattr("converter.routes.probe_media", fail_probe)

    response = app.test_client().post(
        "/api/convert",
        data={
            "file": (io.BytesIO(b"12345"), "audio.wav"),
            "output_format": "mp3",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert "file size limit" in response.get_json()["error"]
    assert list((tmp_path / "jobs").iterdir()) == []


def test_oversized_request_returns_json_error():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "MAX_CONTENT_LENGTH": 64,
        }
    )

    response = app.test_client().post(
        "/api/convert",
        data={"file": (io.BytesIO(b"x" * 100), "too-large.wav"), "output_format": "mp3"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert "500 MB" in response.get_json()["error"]
