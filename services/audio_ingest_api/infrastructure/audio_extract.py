import subprocess
from pathlib import Path
from uuid import uuid4

from audio_ingest_api.application.errors import ApplicationError


class FfmpegAudioExtractor:
    def __init__(self, processed_dir: Path):
        self._processed_dir = processed_dir

    def extract_audio(self, source_path: Path, source_filename: str) -> Path:
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(source_filename).stem or "audio"
        target = self._processed_dir / f"{uuid4().hex}_{stem}.wav"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(target),
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        if process.returncode != 0:
            raise ApplicationError(f"ffmpeg failed: {process.stderr.strip()}", status_code=400)
        return target

