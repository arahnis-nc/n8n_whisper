import json
import subprocess
from pathlib import Path

from audio_ingest_api.application.dto import MediaKind


class FfprobeMediaProbe:
    def detect_kind(self, source_path: Path) -> MediaKind:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(source_path),
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        if process.returncode != 0:
            return "unknown"

        payload = json.loads(process.stdout or "{}")
        streams = payload.get("streams", [])
        has_video = any(stream.get("codec_type") == "video" for stream in streams)
        has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
        if has_video:
            return "video"
        if has_audio:
            return "audio"
        return "unknown"

