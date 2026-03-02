import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    records_dir: Path
    uploads_dir: Path
    transcripts_dir: Path
    whisper_cache_dir: Path
    whisper_device: str
    huggingface_token: str

    @classmethod
    def from_env(cls) -> "Settings":
        records_dir = Path(os.getenv("WHISPER_RECORDS_DIR", "/data/records")).resolve()
        return cls(
            records_dir=records_dir,
            uploads_dir=records_dir / "_uploads",
            transcripts_dir=records_dir / "_transcripts",
            whisper_cache_dir=Path(
                os.getenv("WHISPER_CACHE_DIR", "/root/.cache/whisper")
            ).resolve(),
            whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
            huggingface_token=os.getenv("HUGGINGFACE_TOKEN", ""),
        )

