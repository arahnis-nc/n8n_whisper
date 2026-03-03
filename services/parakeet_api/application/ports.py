from pathlib import Path
from typing import Protocol


class PathResolverPort(Protocol):
    def resolve_input_file(self, relative_path: str) -> Path: ...

    def to_relative(self, absolute_path: Path) -> str: ...


class UploadStoragePort(Protocol):
    async def save_upload(self, filename: str | None, content: bytes) -> Path: ...

    def delete_if_exists(self, target: Path) -> None: ...


class AsrTranscriberPort(Protocol):
    def transcribe(self, source_path: Path, model_name: str, language: str | None) -> str: ...
