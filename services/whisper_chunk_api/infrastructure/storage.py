import shutil
from pathlib import Path
from tempfile import mkdtemp

from whisper_chunk_api.application.errors import ApplicationError, NotFoundError


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


class TempWorkspace:
    def create_temp_dir(self, prefix: str) -> Path:
        return Path(mkdtemp(prefix=prefix))

    def remove_tree(self, target: Path) -> None:
        shutil.rmtree(target, ignore_errors=True)
