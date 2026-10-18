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

On Linux:

```bash
sudo apt install ffmpeg
```

On Fedora and related distributions, use `sudo dnf install ffmpeg` instead. 

On Windows:

Install `ffmpeg` and make sure `ffmpeg` works in a new terminal. One way to install it is:

```bat
winget install Gyan.FFmpeg
```

## Download a video

With the virtual environment activated, from the project folder:

```bash
python download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

The same command works on Linux and Windows. The finished file is written to `videos` in the folder where you ran the command. PyInstaller is not involved in this step.

Create the virtual environment once before the first download.

macOS and Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Executable

Give someone the executable file. They do not clone this project, install Python, or activate a virtual environment. They put the file anywhere and pass the URL.

macOS, for the Apple Silicon build in `dist/download_video`:

```bash
./download_video "https://www.youtube.com/watch?v=VIDEO_ID"
```

Windows, after `dist\download_video.exe` has been built:

```bat
download_video.exe "https://www.youtube.com/watch?v=VIDEO_ID"
```

`ffmpeg` still has to be installed on that computer. The executable includes Python and the download libraries, and it calls `ffmpeg` when a video comes as separate picture and sound tracks. A Mac file does not run on Windows, and a Windows file does not run on a Mac. The Mac file runs on the same Mac architecture it was built on.

The executable is not stored in git. Send the file directly, or attach it to a release. Building it is a separate step and is the only time a virtual environment is used.

macOS:

```bash
source venv/bin/activate
pip install pyinstaller
pyinstaller --noconfirm download_video.spec
```

Windows:

```bat
venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconfirm download_video.spec
```

## Tests

With the virtual environment activated:

```bash
pytest
```
