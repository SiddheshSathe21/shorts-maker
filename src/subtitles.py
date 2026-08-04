"""
subtitles.py
Builds an .ass subtitle file for a single clip, grouping words into short
caption lines and highlighting the currently-spoken word -- the
TikTok/Cliphi "word-pop" style. ASS is used instead of plain .srt because
.srt has no per-word timing or color control.

All timestamps are shifted so that 0 = the clip's own start time, since
the rendered clip is a standalone file that starts at 0.
"""

import os

ASS_HEADER = """[Script Info]
Title: Auto-generated subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,90,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:01d}:{m:02d}:{s:05.2f}"


def _words_in_range(words: list[dict], clip_start: float, clip_end: float) -> list[dict]:
    return [w for w in words if w["end"] > clip_start and w["start"] < clip_end]


def generate_word_pop_ass(
    words: list[dict],
    clip_start: float,
    clip_end: float,
    out_path: str,
    group_size: int = 4,
    highlight_color: str = "&H00FFFF&",  # ASS is &HBBGGRR& -- this is yellow
) -> str:
    """
    Groups consecutive words into lines of `group_size`, and for the
    duration each word is spoken, re-renders that line with the active
    word colored. group_size=4 keeps lines short and punchy; raise it for
    denser captions.
    """
    clip_words = _words_in_range(words, clip_start, clip_end)
    dialogue_lines = []

    for i in range(0, len(clip_words), group_size):
        group = clip_words[i : i + group_size]
        if not group:
            continue

        for idx, w in enumerate(group):
            w_start = max(w["start"] - clip_start, 0)
            w_end = min(w["end"] - clip_start, clip_end - clip_start)
            if w_end <= w_start:
                continue

            parts = []
            for j, gw in enumerate(group):
                if j == idx:
                    parts.append("{\\c" + highlight_color + "}" + gw["word"] + "{\\c&HFFFFFF&}")
                else:
                    parts.append(gw["word"])
            text = " ".join(parts)

            dialogue_lines.append(
                f"Dialogue: 0,{_fmt_time(w_start)},{_fmt_time(w_end)},Default,,0,0,0,,{text}"
            )

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        f.write("\n".join(dialogue_lines))

    return out_path
