from pathlib import Path
from uuid import uuid4

from parakeet_api.application.errors import ApplicationError, NotFoundError


class RecordsPathResolver:
    def __init__(self, records_dir: Path):
        self._records_dir = records_dir.resolve()

    def resolve_input_file(self, relative_path: str) -> Path:
        candidate = (self._records_dir / relative_path).resolve()
        if self._records_dir not in candidate.parents:
            raise ApplicationError("Path must stay inside records directory", status_code=400)
        if not candidate.is_file():
            raise NotFoundError(f"File not found: {relative_path}")
        return candidate

    def to_relative(self, absolute_path: Path) -> str:
        return str(absolute_path.resolve().relative_to(self._records_dir))


class LocalUploadStorage:
    def __init__(self, uploads_dir: Path):
        self._uploads_dir = uploads_dir

    async def save_upload(self, filename: str | None, content: bytes) -> Path:
        self._uploads_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename or "audio.bin").name
        target = self._uploads_dir / f"{uuid4().hex}_{safe_name}"
        target.write_bytes(content)
        return target

    def delete_if_exists(self, target: Path) -> None:
        if target.exists():
            target.unlink(missing_ok=True)
