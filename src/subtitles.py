"""
subtitles.py
Builds an .ass subtitle file for a clip, grouping words into short
caption lines and highlighting the currently-spoken word -- the
TikTok/Cliphi "word-pop" style. ASS is used instead of plain .srt because
.srt has no per-word timing or color/style control.

All timestamps are shifted so that 0 = the clip's own start time, since
the rendered clip is a standalone file that starts at 0.
"""

import os

# ---------------------------------------------------------------------------
# Style presets. Colors are in ASS format: &HAABBGGRR& (alpha, blue, green,
# red -- note the reversed order vs normal RGB). Alpha 00 = opaque, FF = fully
# transparent. Pick a preset by name, or pass your own kwargs to override
# any individual field -- see generate_word_pop_ass().
# ---------------------------------------------------------------------------
STYLE_PRESETS = {
    # white text, active word pops yellow -- classic TikTok look
    "bold_yellow": dict(
        font_name="Arial Black",
        font_size=90,
        text_color="&H00FFFFFF",       # white
        highlight_color="&H0000FFFF",  # yellow
        outline_color="&H00000000",    # black outline
        back_color="&H80000000",       # semi-transparent shadow
        outline_width=4,
        shadow=2,
        bold=True,
        alignment=2,                   # bottom-center
        margin_v=120,
    ),
    # clean white-on-black, active word turns green -- minimal, high readability
    "clean_white": dict(
        font_name="Arial",
        font_size=80,
        text_color="&H00FFFFFF",
        highlight_color="&H0000FF00",  # green
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=3,
        shadow=1,
        bold=True,
        alignment=2,
        margin_v=140,
    ),
    # active word pops pink, positioned higher up (out of the way of on-screen UI/faces)
    "pink_pop_top": dict(
        font_name="Arial Black",
        font_size=85,
        text_color="&H00FFFFFF",
        highlight_color="&H00A155F7",  # pink
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=4,
        shadow=2,
        bold=True,
        alignment=8,                   # top-center
        margin_v=160,
    ),
    # bold red highlight, big font, for high-energy content
    "hype_red": dict(
        font_name="Arial Black",
        font_size=100,
        text_color="&H00FFFFFF",
        highlight_color="&H000000FF",  # red
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=5,
        shadow=2,
        bold=True,
        alignment=2,
        margin_v=120,
    ),
}


def _build_ass_header(
    font_name: str,
    font_size: int,
    text_color: str,
    outline_color: str,
    back_color: str,
    outline_width: int,
    shadow: int,
    bold: bool,
    alignment: int,
    margin_v: int,
) -> str:
    bold_flag = 1 if bold else 0
    return f"""[Script Info]
Title: Auto-generated subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{text_color},&H0000FFFF,{outline_color},{back_color},{bold_flag},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},60,60,{margin_v},1

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
    style: str = "bold_yellow",
    **style_overrides,
) -> str:
    """
    Groups consecutive words into lines of `group_size`, and for the
    duration each word is spoken, re-renders that line with the active
    word colored.

    style: name of a preset in STYLE_PRESETS ("bold_yellow", "clean_white",
    "pink_pop_top", "hype_red"). Pass any field name as a kwarg to override
    just that one value, e.g.:
        generate_word_pop_ass(..., style="clean_white", font_size=100)
    """
    if style not in STYLE_PRESETS:
        raise ValueError(f"Unknown style '{style}'. Options: {list(STYLE_PRESETS)}")

    cfg = {**STYLE_PRESETS[style], **style_overrides}
    header = _build_ass_header(
        font_name=cfg["font_name"],
        font_size=cfg["font_size"],
        text_color=cfg["text_color"],
        outline_color=cfg["outline_color"],
        back_color=cfg["back_color"],
        outline_width=cfg["outline_width"],
        shadow=cfg["shadow"],
        bold=cfg["bold"],
        alignment=cfg["alignment"],
        margin_v=cfg["margin_v"],
    )

    # style-level text_color (&HAABBGGRR&) needs converting to the override-tag
    # format (&HBBGGRR&, no alpha) used inline for the highlight color
    highlight_override = "&H" + cfg["highlight_color"][4:] + "&"
    default_override = "&H" + cfg["text_color"][4:] + "&"

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
                    parts.append("{\\c" + highlight_override + "}" + gw["word"] + "{\\c" + default_override + "}")
                else:
                    parts.append(gw["word"])
            text = " ".join(parts)

            dialogue_lines.append(
                f"Dialogue: 0,{_fmt_time(w_start)},{_fmt_time(w_end)},Default,,0,0,0,,{text}"
            )

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(dialogue_lines))

    return out_path
