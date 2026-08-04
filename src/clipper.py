"""
clipper.py
Cuts an exact clip out of the source video and burns in the subtitle
file, optionally center-cropping to vertical 9:16. This is the "exact,
accurate" part of the pipeline -- ffmpeg's -ss placed *before* -i is
still frame-accurate when combined with re-encoding (which we're doing
anyway, since we're burning subtitles and cropping), so clip boundaries
land exactly where the transcript says they should.
"""

import os
import subprocess


def cut_and_caption(
    video_path: str,
    clip_start: float,
    clip_end: float,
    ass_path: str,
    output_path: str,
    vertical: bool = True,
    target_width: int = 1080,
    target_height: int = 1920,
) -> str:
    duration = clip_end - clip_start
    if duration <= 0:
        raise ValueError(f"clip_end ({clip_end}) must be after clip_start ({clip_start})")

    vf_filters = []
    if vertical:
        # scale so height matches target, then center-crop width.
        # this is a plain center crop -- no speaker tracking yet (phase 3).
        vf_filters.append(f"scale=-2:{target_height}:force_original_aspect_ratio=increase")
        vf_filters.append(f"crop={target_width}:{target_height}")

    # ffmpeg's ass filter needs a path without characters that break its
    # internal arg parsing (colons on windows, etc) -- escape defensively
    escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
    vf_filters.append(f"ass={escaped_ass_path}")

    vf = ",".join(vf_filters)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(clip_start),
        "-i", video_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-3000:]}")

    return output_path
