import os
import tempfile
from pathlib import Path
from typing import List

import streamlit as st
from faster_whisper import WhisperModel
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Video Transcriber", page_icon="🎬", layout="wide")

st.title("🎬 Universal Video Transcriber")
st.caption(
    "Drop a video file or paste YouTube/TikTok/other links, then transcribe and copy the text."
)

if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0
if "links_input" not in st.session_state:
    st.session_state.links_input = ""
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "status_log" not in st.session_state:
    st.session_state.status_log = []


@st.cache_resource(show_spinner=False)
def load_model() -> WhisperModel:
    return WhisperModel("small", compute_type="int8")


def transcribe_media(path: str) -> str:
    model = load_model()
    segments, _ = model.transcribe(path, vad_filter=True, beam_size=5)
    return "\n".join(segment.text.strip() for segment in segments if segment.text.strip())


def download_link_media(url: str, out_dir: Path) -> Path:
    out_template = str(out_dir / "%(title).120s.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded = ydl.prepare_filename(info)

    base, _ = os.path.splitext(downloaded)
    mp3_candidate = Path(f"{base}.mp3")
    return mp3_candidate if mp3_candidate.exists() else Path(downloaded)


def split_links(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


left, right = st.columns(2)

with left:
    st.subheader("Upload video")
    uploaded_file = st.file_uploader(
        "Drag and drop any video file",
        type=["mp4", "mov", "mkv", "avi", "webm", "m4v", "mp3", "wav", "m4a"],
        key=f"uploader_{st.session_state.uploader_version}",
    )

with right:
    st.subheader("Video links")
    st.text_area(
        "Paste one link per line (YouTube, TikTok, etc.)",
        key="links_input",
        height=160,
        placeholder="https://www.youtube.com/watch?v=...\nhttps://www.tiktok.com/@.../video/...",
    )

controls = st.columns(4)

if controls[0].button("Transcribe Uploaded Video", use_container_width=True):
    if not uploaded_file:
        st.warning("Please drop a video/audio file first.")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / uploaded_file.name
            input_path.write_bytes(uploaded_file.read())
            with st.spinner("Transcribing uploaded media..."):
                try:
                    text = transcribe_media(str(input_path))
                    st.session_state.transcript = text
                    st.session_state.status_log.append(f"✅ Transcribed upload: {uploaded_file.name}")
                except Exception as exc:
                    st.error(f"Failed to transcribe uploaded media: {exc}")

if controls[1].button("Transcribe Links", use_container_width=True):
    links = split_links(st.session_state.links_input)
    if not links:
        st.warning("Please paste at least one link first.")
    else:
        collected = []
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for idx, url in enumerate(links, start=1):
                with st.spinner(f"Downloading + transcribing link {idx}/{len(links)}..."):
                    try:
                        media_path = download_link_media(url, tmp_dir)
                        text = transcribe_media(str(media_path))
                        collected.append(f"### Source: {url}\n{text}")
                        st.session_state.status_log.append(f"✅ Transcribed link: {url}")
                    except Exception as exc:
                        st.session_state.status_log.append(f"❌ Failed link: {url} ({exc})")
            if collected:
                st.session_state.transcript = "\n\n".join(collected)

if controls[2].button("Clear Links + Drag Content", use_container_width=True):
    st.session_state.links_input = ""
    st.session_state.uploader_version += 1
    st.session_state.status_log.append("🧹 Cleared links and uploader content")
    st.rerun()

if controls[3].button("Clear Transcript", use_container_width=True):
    st.session_state.transcript = ""
    st.session_state.status_log.append("🧼 Cleared transcript")

st.divider()
st.subheader("Transcript")
st.text_area(
    "Transcribed text (copy this)",
    value=st.session_state.transcript,
    height=320,
    placeholder="Your transcript appears here...",
)

if st.session_state.transcript:
    st.download_button(
        "Download transcript (.txt)",
        data=st.session_state.transcript.encode("utf-8"),
        file_name="transcript.txt",
        mime="text/plain",
    )

if st.session_state.status_log:
    st.subheader("Activity")
    for item in reversed(st.session_state.status_log[-10:]):
        st.write(item)

st.info(
    "Tip: The first transcription may be slower while the speech model downloads. "
    "For very long videos, leave the tab open until processing completes."
)
