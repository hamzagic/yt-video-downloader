import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pytubefix import YouTube
from pytubefix.cli import on_progress

def download_stream(stream, output_dir, filename):
  """Download a stream in chunks sized from the known file length.

  pytubefix probes the file with range=0-99999999999, and YouTube responds
  403 to that request for some Shorts.
  """
  file_path = Path(output_dir) / filename
  file_size = stream.filesize
  downloaded = 0
  chunk_size = 9437184
  with open(file_path, "wb") as file_handle:
    while downloaded < file_size:
      stop = min(downloaded + chunk_size, file_size) - 1
      request = Request(
        f"{stream.url}&range={downloaded}-{stop}",
        headers={"User-Agent": "Mozilla/5.0", "accept-language": "en-US,en"},
      )
      for attempt in range(3):
        try:
          with urlopen(request) as response:
            expected = stop - downloaded + 1
            received = 0
            while received < expected:
              chunk = response.read(min(65536, expected - received))
              if not chunk:
                break
              received += len(chunk)
              downloaded += len(chunk)
              stream.on_progress(chunk, file_handle, file_size - downloaded)
          break
        except HTTPError as error:
          if error.code != 403 or attempt == 2:
            raise
  return str(file_path)

def download_video(url: str):
  url = url.strip()
  if not url:
    raise ValueError("URL is required")
  if not (
      url.startswith("https://www.youtube.com/watch?v=")
      or url.startswith("https://www.youtube.com/shorts/")
  ):
    raise ValueError("Invalid URL")
  
  output_dir = Path("./videos")
  output_dir.mkdir(parents=True, exist_ok=True)
  output_file = output_dir / "video.mp4"
  yt = YouTube(url, on_progress_callback=on_progress)
  print(yt.title)

  stream = yt.streams.get_highest_resolution()
  if stream is not None:
      print(f"Downloading {stream.title} to {output_file.name}!")
      stream.download(output_path=str(output_file))
  else:
      print("No stream found, downloading video and audio separately!")
      output_file = output_dir / f"{yt.title}.mp4"
      video = (
          yt.streams.filter(only_video=True, file_extension="mp4")
          .order_by("resolution")
          .last()
      )
      audio = (
          yt.streams.filter(only_audio=True, file_extension="mp4")
          .order_by("abr")
          .last()
      )
      video_path = download_stream(video, output_dir, "video_only.mp4")
      audio_path = download_stream(audio, output_dir, "audio_only.mp4")
      subprocess.run(
          [
              "ffmpeg",
              "-y",
              "-i",
              video_path,
              "-i",
              audio_path,
              "-c",
              "copy",
              str(output_file),
          ],
          check=True,
      )
      Path(video_path).unlink()
      Path(audio_path).unlink()
