import os
import sys

from main import download_video


def usage_line():
    if getattr(sys, "frozen", False):
        program = "download_video.exe" if os.name == "nt" else "download_video"
        return f'Usage: {program} "<url>"'
    return 'Usage: python download_video.py "<url>"'


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print(usage_line())
        raise SystemExit(1)
    download_video(arguments[0])


if __name__ == "__main__":
    main()
