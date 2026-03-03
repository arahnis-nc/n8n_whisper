import subprocess
from pathlib import Path

from whisper_chunk_api.application.errors import ApplicationError


class FfmpegChunker:
    def chunk_to_wav(self, source: Path, chunk_seconds: int, output_dir: Path) -> list[Path]:
        pattern = str(output_dir / "chunk_%05d.wav")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            pattern,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise ApplicationError(f"ffmpeg failed: {proc.stderr[:500]}", status_code=400)
        return sorted(output_dir.glob("chunk_*.wav"))
