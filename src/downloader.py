"""
downloader.py
Downloads a YouTube video with yt-dlp, capped at a max resolution so we
never pull down more data than a shorts pipeline needs (no point grabbing
4K when the output is a 1080x1920 crop).
"""

import os
import yt_dlp


def download_video(
    url: str,
    output_dir: str = "downloads",
    max_height: int = 720,
    cookiefile: str | None = None,
) -> tuple[str, dict]:
    """
    Downloads `url` and returns (path_to_mp4, info_dict).

    max_height=720 is plenty for shorts output. Lower it to 480 if you
    want to save even more bandwidth/disk on a Colab session.

    cookiefile: path to a cookies.txt exported from your own logged-in
    browser (e.g. via the "Get cookies.txt LOCALLY" extension). YouTube
    often blocks cloud IPs like Colab's with a "confirm you're not a bot"
    error -- passing real cookies fixes this. Leave as None if you're not
    hitting that error.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,
        "noplaylist": True,
    }

    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)

        # after ffmpeg merges audio+video the extension becomes .mp4;
        # prepare_filename() doesn't know that, so correct it here
        base, _ext = os.path.splitext(filepath)
        mp4_path = base + ".mp4"
        if os.path.exists(mp4_path):
            filepath = mp4_path

        return filepath, info


def cleanup_video(path: str) -> None:
    """Deletes the full downloaded video once you're done cutting clips
    from it. Call this explicitly -- we never auto-delete, since you might
    want to cut multiple clips from the same source video first."""
    if path and os.path.exists(path):
        os.remove(path)
