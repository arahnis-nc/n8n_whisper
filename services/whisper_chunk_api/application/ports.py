from pathlib import Path
from typing import Protocol


class PathResolverPort(Protocol):
    def resolve_input_file(self, relative_path: str) -> Path: ...

    def to_relative(self, absolute_path: Path) -> str: ...


class ChunkerPort(Protocol):
    def chunk_to_wav(self, source: Path, chunk_seconds: int, output_dir: Path) -> list[Path]: ...


class TranscriberPort(Protocol):
    def transcribe(
        self,
        *,
        chunk_path: Path,
        backend: str,
        model: str,
        cloud_model: str,
        language: str | None,
        task: str,
        prompt: str | None,
        temperature: float,
    ) -> str: ...


class WorkspacePort(Protocol):
    def create_temp_dir(self, prefix: str) -> Path: ...

    def remove_tree(self, target: Path) -> None: ...


class TranscriptPostprocessorPort(Protocol):
    def postprocess(self, *, text: str, language: str | None) -> str: ...
