from typing import Any

from whisper_chunk_api.application.dto import ChunkTranscribeCommand
from whisper_chunk_api.application.errors import ApplicationError
from whisper_chunk_api.application.ports import ChunkerPort, PathResolverPort, TranscriberPort, WorkspacePort


class TranscribeChunksUseCase:
    def __init__(
        self,
        *,
        path_resolver: PathResolverPort,
        chunker: ChunkerPort,
        transcriber: TranscriberPort,
        workspace: WorkspacePort,
    ):
        self._path_resolver = path_resolver
        self._chunker = chunker
        self._transcriber = transcriber
        self._workspace = workspace

    def execute(self, command: ChunkTranscribeCommand) -> dict[str, Any]:
        source = self._path_resolver.resolve_input_file(command.path)
        temp_dir = self._workspace.create_temp_dir(prefix="whisper_chunks_")
        try:
            chunks = self._chunker.chunk_to_wav(source, command.chunk_seconds, temp_dir)
            if not chunks:
                raise ApplicationError("No chunks produced from audio", status_code=400)

            parts: list[dict[str, Any]] = []
            full_text_parts: list[str] = []
            for idx, chunk in enumerate(chunks):
                text = self._transcriber.transcribe(
                    chunk_path=chunk,
                    backend=command.backend,
                    model=command.model,
                    cloud_model=command.cloud_model,
                    language=command.language,
                    task=command.task,
                    prompt=command.prompt,
                    temperature=command.temperature,
                )
                parts.append({"index": idx, "file": chunk.name, "text": text})
                if text:
                    full_text_parts.append(text)

            return {
                "input_path": self._path_resolver.to_relative(source),
                "backend": command.backend,
                "model": command.cloud_model if command.backend == "cloud" else command.model,
                "task": command.task,
                "language": command.language,
                "chunk_seconds": command.chunk_seconds,
                "chunks_count": len(parts),
                "text": "\n".join(full_text_parts),
                "chunks": parts,
            }
        finally:
            self._workspace.remove_tree(temp_dir)
