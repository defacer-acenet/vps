#install: pip install -U yt-dlp
import argparse
import re
import sys
import shutil
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


PLATFORMS = {
    "0": "YouTube",
    "1": "SoundCloud",
    "2": "TikTok",
}

ALLOWED_HOSTS = {
    "0": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "1": ("soundcloud.com",),
    "2": ("tiktok.com",),
}


def clean_filename(name):
    """Remove characters that are invalid in filenames."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip(" .")[:180] or "audio"


def progress_hook(data):
    """Display download progress, speed, and file size."""
    status = data.get("status")

    if status == "downloading":
        percent = data.get("_percent_str", " ?%").strip()
        speed = data.get("_speed_str", "Unknown").strip()
        size = (
            data.get("_total_bytes_str")
            or data.get("_total_bytes_estimate_str")
            or "Unknown"
        )

        try:
            value = float(percent.replace("%", "").strip())
            filled = int(28 * value / 100)
            bar = "#" * filled + "-" * (28 - filled)
        except (ValueError, TypeError):
            bar = "-" * 28

        print(
            f"\r[{bar}] {percent:>7} | {speed} | {size}",
            end="",
            flush=True,
        )

    elif status == "finished":
        print("\nDownload complete. Converting to WAV...")


def main():
    parser = argparse.ArgumentParser(
        description="Download audio and convert it to WAV."
    )

    parser.add_argument(
        "platform",
        choices=["0", "1", "2"],
        help="0 = YouTube, 1 = SoundCloud, 2 = TikTok",
    )
    parser.add_argument("url", help="Video or audio URL")
    parser.add_argument(
        "--path",
        "-p",
        default="downloads",
        help="Output directory (default: downloads)",
    )

    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit(
            "Error: FFmpeg was not found. "
            "Install FFmpeg and add it to your system PATH."
        )

    parsed = urlparse(args.url)
    host = (parsed.hostname or "").lower()

    if parsed.scheme not in ("http", "https"):
        sys.exit("Error: URL must start with http:// or https://.")

    if not any(
        host == domain or host.endswith("." + domain)
        for domain in ALLOWED_HOSTS[args.platform]
    ):
        sys.exit(
            f"Error: URL does not match {PLATFORMS[args.platform]}."
        )

    output_dir = Path(args.path).expanduser()

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        sys.exit(f"Error creating output directory: {error}")

    print(f"Platform: {PLATFORMS[args.platform]}")
    print(f"URL: {args.url}")
    print(f"Output directory: {output_dir.resolve()}")
    print("Format: WAV PCM 16-bit, 44.1 kHz, stereo\n")

    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "postprocessor_args": [
            "-ar", "44100",
            "-ac", "2",
            "-c:a", "pcm_s16le",
        ],
        "quiet": True,
        "no_warnings": False,
        "overwrites": False,
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(args.url, download=True)

        title = clean_filename(info.get("title", "audio"))
        video_id = info.get("id", "")

        candidates = list(output_dir.glob(f"{video_id}*.wav"))

        if not candidates:
            sys.exit(
                "Error: WAV output was not found. "
                "Check the yt-dlp and FFmpeg messages."
            )

        source = candidates[0]
        target = output_dir / f"{title}.wav"

        if source.resolve() != target.resolve():
            if target.exists():
                target = output_dir / f"{title}_{video_id}.wav"
            source.rename(target)

        print("\nSUCCESS!")
        print(f"Title: {info.get('title', 'Unknown')}")
        print(f"Output file: {target.resolve()}")
        print(f"File size: {target.stat().st_size / 1024**2:.2f} MB")

    except KeyboardInterrupt:
        print("\nDownload cancelled.")
        sys.exit(130)

    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
