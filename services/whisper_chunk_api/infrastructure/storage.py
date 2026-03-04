import shutil
from pathlib import Path
from tempfile import mkdtemp

from whisper_chunk_api.application.errors import ApplicationError, NotFoundError


class RecordsPathResolver:
    def __init__(self, records_dir: Path, allowed_input_dirs: list[Path] | None = None):
        self._records_dir = records_dir.resolve()
        roots = allowed_input_dirs or [self._records_dir]
        self._allowed_roots = [root.resolve() for root in roots]

    def resolve_input_file(self, relative_path: str) -> Path:
        raw = Path(relative_path)
        candidate = raw.resolve() if raw.is_absolute() else (self._records_dir / raw).resolve()
        if not any(root == candidate or root in candidate.parents for root in self._allowed_roots):
            raise ApplicationError("Path must stay inside allowed input directories", status_code=400)
        if not candidate.is_file():
            raise NotFoundError(f"File not found: {relative_path}")
        return candidate

    def to_relative(self, absolute_path: Path) -> str:
        resolved = absolute_path.resolve()
        try:
            return str(resolved.relative_to(self._records_dir))
        except ValueError:
            return str(resolved)


class TempWorkspace:
    def create_temp_dir(self, prefix: str) -> Path:
        return Path(mkdtemp(prefix=prefix))

    def remove_tree(self, target: Path) -> None:
        shutil.rmtree(target, ignore_errors=True)
