"""
transcriber.py
Runs faster-whisper on the downloaded video to get a transcript with
word-level timestamps. This is what makes accurate word-by-word
subtitles possible -- without word timestamps you can only caption at
the sentence level, which looks nothing like the TikTok/Cliphi style.
"""

import json
from faster_whisper import WhisperModel


def transcribe(
    video_path: str,
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "int8",
) -> dict:
    """
    model_size options (speed/accuracy tradeoff): tiny, base, small,
    medium, large-v3. On Colab's free GPU, "small" or "medium" is a good
    balance. Use "cuda" for device if you confirmed a GPU runtime,
    otherwise "cpu" -- "auto" tries cuda and falls back automatically.
    """
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(video_path, word_timestamps=True)

    words = []
    full_segments = []

    for seg in segments:
        seg_words = []
        for w in seg.words:
            entry = {"word": w.word.strip(), "start": w.start, "end": w.end}
            words.append(entry)
            seg_words.append(entry)

        full_segments.append(
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": seg_words,
            }
        )

    return {"language": info.language, "segments": full_segments, "words": words}


def save_transcript(transcript: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)


def load_transcript(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_segments(transcript: dict) -> None:
    """Prints [mm:ss - mm:ss] text for every segment so you can eyeball
    the transcript and pick clip start/end times manually."""

    def fmt(t: float) -> str:
        m, s = divmod(int(t), 60)
        return f"{m:02d}:{s:02d}"

    for seg in transcript["segments"]:
        print(f"[{fmt(seg['start'])} - {fmt(seg['end'])}] {seg['text']}")
