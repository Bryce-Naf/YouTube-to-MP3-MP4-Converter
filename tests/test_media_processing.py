import json
import subprocess
from types import SimpleNamespace

import pytest

from converter.media_processing import (
    MediaInfo,
    MediaValidationError,
    convert_media,
    probe_media,
)


def test_probe_rejects_extension_that_does_not_match_media(monkeypatch, tmp_path):
    probe_output = {
        "format": {"format_name": "mp3", "duration": "3"},
        "streams": [{"codec_type": "audio"}],
    }
    def fake_run(arguments, **options):
        assert arguments[0] == "ffprobe"
        assert options["check"] is True
        return SimpleNamespace(stdout=json.dumps(probe_output))

    monkeypatch.setattr("converter.media_processing.subprocess.run", fake_run)

    with pytest.raises(MediaValidationError, match="extension does not match"):
        probe_media(tmp_path / "not-really-mp4.mp4")


def test_audio_to_mp4_adds_black_video_background(monkeypatch, tmp_path):
    command = []

    def fake_run(arguments, **options):
        assert arguments[0] == "ffmpeg"
        assert options["check"] is True
        assert options["timeout"] > 0
        command.extend(arguments)
        (tmp_path / "converted.mp4").write_bytes(b"converted")
        return subprocess.CompletedProcess(arguments, 0, stdout="", stderr="")

    monkeypatch.setattr("converter.media_processing.subprocess.run", fake_run)

    convert_media(
        tmp_path / "source.mp3",
        tmp_path / "converted.mp4",
        "mp4",
        MediaInfo(frozenset({"mp3"}), frozenset({"audio"}), 3.0),
    )

    assert "color=c=black:s=1280x720:r=30" in command
    assert "libx264" in command
