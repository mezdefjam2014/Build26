# Universal Video Transcriber

A Streamlit app that can:
- Drag-and-drop upload video/audio files of practically any length (server limit is configurable).
- Accept links (YouTube, TikTok, and many other sites supported by `yt-dlp`).
- Transcribe media to text with `faster-whisper`.
- Copy or download transcript output.
- Clear links, upload content, and transcript state quickly.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- First run downloads a Whisper model.
- URL extraction depends on source website support in `yt-dlp`.
