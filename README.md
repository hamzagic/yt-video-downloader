# YT VIDEO DOWNLOADER

A script that downloads a YouTube video or Short into a `videos` folder.

It accepts these URLs:

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

Put the URL in quotes. A link that contains `&` will otherwise be split by the terminal.

When YouTube provides one file that already contains picture and sound, that file is saved. When picture and sound come as separate tracks, the script downloads both and merges them with `ffmpeg`. The merged file is named after the video title.

## Requirements

- Python 3.11 or newer
- `ffmpeg` on the command path

On macOS:

```bash
brew install ffmpeg
```

On Windows, install `ffmpeg` and make sure `ffmpeg` works in a new terminal. One way to install it is:

```bat
winget install Gyan.FFmpeg
```

## Run the Python project

From the project folder:

macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Windows:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

The finished file is written to `videos` in the folder where you ran the command.

## Executable

The executable takes the same URL and does not need a separate Python environment. It still needs `ffmpeg` installed. Build it on the system where it will run. A Mac build does not run on Windows, and a Windows build does not run on a Mac.

macOS, from the project folder with the virtual environment activated:

```bash
pip install pyinstaller
pyinstaller --noconfirm download_video.spec
./dist/download_video "https://www.youtube.com/watch?v=VIDEO_ID"
```

The Mac executable runs on the same Mac architecture it was built on.

Windows, from the project folder with the virtual environment activated:

```bat
pip install pyinstaller
pyinstaller --noconfirm download_video.spec
dist\download_video.exe "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Tests

With the virtual environment activated:

```bash
pytest
```
