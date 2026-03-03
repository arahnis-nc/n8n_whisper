import shutil
from pathlib import Path
from uuid import uuid4


class LocalUploadStorage:
    def __init__(self, uploads_dir: Path):
        self._uploads_dir = uploads_dir

    async def save_upload(self, filename: str | None, content: bytes) -> Path:
        self._uploads_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename or "upload.bin").name
        target = self._uploads_dir / f"{uuid4().hex}_{safe_name}"
        target.write_bytes(content)
        return target


class RuntimeAudioStorage:
    def __init__(self, processed_dir: Path):
        self._processed_dir = processed_dir

    def persist_audio(self, source_path: Path, source_filename: str) -> Path:
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(source_filename).name
        target = self._processed_dir / f"{uuid4().hex}_{safe_name}"
        shutil.copy2(source_path, target)
        return target

