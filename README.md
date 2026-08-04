# Shorts Maker

Turns a long YouTube video into a short clip with accurate, word-by-word
burned-in captions -- runs entirely on Google Colab's free disk/GPU, so it
works fine even on a low-storage or older laptop. Nothing but the final
clip ever touches your machine.

## How it works

1. `src/downloader.py` -- pulls the video with `yt-dlp`, capped at 720p
2. `src/transcriber.py` -- transcribes with `faster-whisper`, word-level timestamps
3. `src/subtitles.py` -- builds a TikTok-style word-pop `.ass` subtitle file
4. `src/clipper.py` -- cuts the exact clip with `ffmpeg`, crops to vertical 9:16, burns in the subtitles
5. `notebook/ShortsMaker.ipynb` -- the Colab notebook that ties it all together

Right now you pick the clip's start/end time yourself by reading the
printed transcript (phase 1). Phase 2 will add AI-suggested highlight
moments so you don't have to scrub manually.

## Setup

1. Push this repo to your own GitHub account.
2. Open `notebook/ShortsMaker.ipynb` in Google Colab (File -> Upload
   notebook, or open directly from GitHub via Colab's GitHub tab).
3. In the notebook, replace `REPO_URL` with your repo's URL.
4. Runtime -> Change runtime type -> GPU (T4 is fine, free tier).
5. Run the cells top to bottom, pasting your YouTube link and clip
   start/end times where marked.

## Storage notes

- Nothing is installed or downloaded on your laptop -- everything lives
  on Colab's temporary disk, which resets when the session ends.
- The full source video is deleted with `cleanup_video()` once you're
  done pulling clips from it (run the last cell).
- Only download the final `.mp4` clips you actually want to keep.

## Roadmap

- [x] Phase 1: download, transcribe, manual clip selection, burned captions
- [ ] Phase 2: AI-suggested highlight moments (LLM scores the transcript)
- [ ] Phase 3: active speaker tracking for the vertical crop (currently a
      plain center crop), style presets, batch processing

## A note on copyright

Only use this on videos you own or have rights to clip.
