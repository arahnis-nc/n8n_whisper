from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TranscribeCommand:
    source_path: Path
    source_is_temporary: bool
    model: str
    language: str | None
