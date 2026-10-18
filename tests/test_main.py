import subprocess
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

import download_video as cli
import main


WATCH_URL = "https://www.youtube.com/watch?v=dEq36Ugv7Io"
SHORTS_URL = "https://www.youtube.com/shorts/LdnuoG0CK48"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.offset = 0

    def read(self, size=-1):
        if size is None or size < 0:
            size = len(self.payload) - self.offset
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStream:
    def __init__(self, url, payload):
        self.url = url
        self.filesize = len(payload)
        self.payload = payload
        self.progress = []

    def on_progress(self, chunk, file_handle, bytes_remaining):
        file_handle.write(chunk)
        self.progress.append(bytes_remaining)


def http_error(url, code):
    return HTTPError(url, code, "error", hdrs=None, fp=None)


def test_empty_url_is_rejected():
    with pytest.raises(ValueError, match="URL is required"):
        main.download_video("   ")


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com/shorts/LdnuoG0CK48",
        "http://www.youtube.com/watch?v=dEq36Ugv7Io",
        "https://youtu.be/dEq36Ugv7Io",
        "not a url",
    ],
)
def test_invalid_url_is_rejected(url):
    with pytest.raises(ValueError, match="Invalid URL"):
        main.download_video(url)


def test_watch_and_shorts_urls_are_accepted(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    seen = []

    def fake_youtube(url, on_progress_callback=None):
        seen.append(url)
        streams = SimpleNamespace(get_highest_resolution=lambda: None, filter=lambda **kwargs: None)
        return SimpleNamespace(title="title", streams=streams)

    monkeypatch.setattr(main, "YouTube", fake_youtube)

    for url in (f"  {WATCH_URL}&t=12  ", SHORTS_URL):
        seen.clear()
        with pytest.raises(AttributeError):
            main.download_video(url)
        assert seen == [url.strip()]


def test_download_stream_writes_the_requested_bytes(monkeypatch, tmp_path):
    payload = b"abcdefghijklmnopqrstuvwxyz"
    stream = FakeStream("https://example.test/video", payload)
    requested = []

    def fake_urlopen(request):
        requested.append(request.full_url)
        start, stop = request.full_url.rsplit("range=", 1)[1].split("-")
        start, stop = int(start), int(stop)
        return FakeResponse(payload[start:stop + 1])

    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    path = main.download_stream(stream, tmp_path, "clip.mp4")

    assert path == str(tmp_path / "clip.mp4")
    assert (tmp_path / "clip.mp4").read_bytes() == payload
    assert requested == [f"{stream.url}&range=0-{len(payload) - 1}"]
    assert stream.progress[-1] == 0
    assert all("99999999999" not in url for url in requested)


def test_download_stream_splits_ranges_on_the_chunk_boundary(monkeypatch, tmp_path):
    chunk_size = 9437184
    payload = b"x" * (chunk_size + 3)
    stream = FakeStream("https://example.test/video", payload)
    requested = []

    def fake_urlopen(request):
        requested.append(request.full_url)
        start, stop = request.full_url.rsplit("range=", 1)[1].split("-")
        return FakeResponse(b"x" * (int(stop) - int(start) + 1))

    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    main.download_stream(stream, tmp_path, "clip.mp4")

    assert requested == [
        f"{stream.url}&range=0-{chunk_size - 1}",
        f"{stream.url}&range={chunk_size}-{chunk_size + 2}",
    ]
    assert (tmp_path / "clip.mp4").read_bytes() == payload


def test_download_stream_retries_a_forbidden_response(monkeypatch, tmp_path):
    payload = b"ok"
    stream = FakeStream("https://example.test/video", payload)
    attempts = []

    def fake_urlopen(request):
        attempts.append(request.full_url)
        if len(attempts) < 3:
            raise http_error(request.full_url, 403)
        return FakeResponse(payload)

    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    main.download_stream(stream, tmp_path, "clip.mp4")

    assert len(attempts) == 3
    assert (tmp_path / "clip.mp4").read_bytes() == payload


def test_download_stream_raises_after_three_forbidden_responses(monkeypatch, tmp_path):
    stream = FakeStream("https://example.test/video", b"ok")
    attempts = []

    def fake_urlopen(request):
        attempts.append(request.full_url)
        raise http_error(request.full_url, 403)

    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    with pytest.raises(HTTPError):
        main.download_stream(stream, tmp_path, "clip.mp4")

    assert len(attempts) == 3


def test_download_stream_does_not_retry_other_http_errors(monkeypatch, tmp_path):
    stream = FakeStream("https://example.test/video", b"ok")
    attempts = []

    def fake_urlopen(request):
        attempts.append(request.full_url)
        raise http_error(request.full_url, 404)

    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    with pytest.raises(HTTPError) as error:
        main.download_stream(stream, tmp_path, "clip.mp4")

    assert error.value.code == 404
    assert len(attempts) == 1


def test_progressive_stream_uses_pytubefix_download(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    downloaded = {}

    def download(output_path, filename):
        downloaded["output_path"] = output_path
        downloaded["filename"] = filename

    stream = SimpleNamespace(title="clip", download=download)
    youtube = SimpleNamespace(
        title="clip",
        streams=SimpleNamespace(get_highest_resolution=lambda: stream),
    )
    monkeypatch.setattr(main, "YouTube", lambda url, on_progress_callback=None: youtube)

    main.download_video(WATCH_URL)

    assert downloaded["output_path"] == "videos"
    assert downloaded["filename"] == Path("videos") / "clip"


def test_separate_streams_are_merged_under_the_video_title(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    title = "'Entire street is a river': Las Vegas"
    video = FakeStream("https://example.test/video", b"video")
    audio = FakeStream("https://example.test/audio", b"audio")

    class Streams:
        def get_highest_resolution(self):
            return None

        def filter(self, only_video=None, only_audio=None, file_extension=None):
            selected = video if only_video else audio
            return SimpleNamespace(order_by=lambda name: SimpleNamespace(last=lambda: selected))

    monkeypatch.setattr(
        main,
        "YouTube",
        lambda url, on_progress_callback=None: SimpleNamespace(title=title, streams=Streams()),
    )

    def fake_download(stream, output_dir, filename):
        path = output_dir / filename
        path.write_bytes(stream.payload)
        return str(path)

    ffmpeg_command = {}

    def fake_run(command, check):
        ffmpeg_command["command"] = command
        ffmpeg_command["check"] = check
        (tmp_path / "videos" / f"{title}.mp4").write_bytes(b"merged")

    monkeypatch.setattr(main, "download_stream", fake_download)
    monkeypatch.setattr(main.subprocess, "run", fake_run)

    main.download_video(SHORTS_URL)

    output = tmp_path / "videos" / f"{title}.mp4"
    assert output.read_bytes() == b"merged"
    assert ffmpeg_command["check"] is True
    assert ffmpeg_command["command"] == [
        "ffmpeg",
        "-y",
        "-i",
        "videos/video_only.mp4",
        "-i",
        "videos/audio_only.mp4",
        "-c",
        "copy",
        str(Path("videos") / f"{title}.mp4"),
    ]
    assert not (tmp_path / "videos" / "video_only.mp4").exists()
    assert not (tmp_path / "videos" / "audio_only.mp4").exists()


def test_merge_failure_is_raised(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    video = FakeStream("https://example.test/video", b"video")
    audio = FakeStream("https://example.test/audio", b"audio")

    class Streams:
        def get_highest_resolution(self):
            return None

        def filter(self, only_video=None, only_audio=None, file_extension=None):
            selected = video if only_video else audio
            return SimpleNamespace(order_by=lambda name: SimpleNamespace(last=lambda: selected))

    monkeypatch.setattr(
        main,
        "YouTube",
        lambda url, on_progress_callback=None: SimpleNamespace(title="title", streams=Streams()),
    )
    monkeypatch.setattr(
        main,
        "download_stream",
        lambda stream, output_dir, filename: str(output_dir / filename),
    )

    def fake_run(command, check):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        main.download_video(SHORTS_URL)


def test_frozen_executable_usage_mentions_the_program_name(capsys, monkeypatch):
    monkeypatch.setattr(cli.sys, "frozen", True, raising=False)

    with pytest.raises(SystemExit):
        cli.main([])

    assert 'download_video "<url>"' in capsys.readouterr().out


def test_windows_executable_usage_uses_the_exe_name(capsys, monkeypatch):
    monkeypatch.setattr(cli.sys, "frozen", True, raising=False)
    monkeypatch.setattr(cli.os, "name", "nt")

    with pytest.raises(SystemExit):
        cli.main([])

    assert 'download_video.exe "<url>"' in capsys.readouterr().out


def test_cli_passes_the_url_to_download_video(monkeypatch):
    seen = []
    monkeypatch.setattr(cli, "download_video", lambda url: seen.append(url))

    cli.main([SHORTS_URL])

    assert seen == [SHORTS_URL]


@pytest.mark.parametrize("arguments", [[], [WATCH_URL, SHORTS_URL]])
def test_cli_requires_exactly_one_url(capsys, arguments):
    with pytest.raises(SystemExit) as error:
        cli.main(arguments)

    assert error.value.code == 1
    assert 'python download_video.py "<url>"' in capsys.readouterr().out
