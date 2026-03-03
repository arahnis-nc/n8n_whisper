from parakeet_api.application.dto import TranscribeCommand
from parakeet_api.application.ports import AsrTranscriberPort, PathResolverPort, UploadStoragePort


class TranscribeAudioUseCase:
    def __init__(
        self,
        *,
        transcriber: AsrTranscriberPort,
        path_resolver: PathResolverPort,
        upload_storage: UploadStoragePort,
    ):
        self._transcriber = transcriber
        self._path_resolver = path_resolver
        self._upload_storage = upload_storage

    def execute(self, command: TranscribeCommand) -> dict[str, str | None]:
        try:
            text = self._transcriber.transcribe(
                source_path=command.source_path,
                model_name=command.model,
                language=command.language,
            )
            return {
                "text": text,
                "model": command.model,
                "language": command.language,
                "input_path": self._path_resolver.to_relative(command.source_path),
            }
        finally:
            if command.source_is_temporary:
                self._upload_storage.delete_if_exists(command.source_path)
