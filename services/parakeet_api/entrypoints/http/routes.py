from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from parakeet_api.application.dto import TranscribeCommand
from parakeet_api.application.errors import ApplicationError
from parakeet_api.application.use_cases.transcribe_audio import TranscribeAudioUseCase
from parakeet_api.entrypoints.http.schemas import DEFAULT_MODEL, TranscribeBody
from parakeet_api.infrastructure.storage import RecordsPathResolver


def build_router(
    *,
    use_case: TranscribeAudioUseCase,
    path_resolver: RecordsPathResolver,
    upload_storage,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/transcribe")
    async def transcribe(
        request: Request,
        file: UploadFile | None = File(default=None),
        model: str = Form(default=DEFAULT_MODEL),
        language: str | None = Form(default=None),
    ):
        content_type = request.headers.get("content-type", "")
        try:
            if content_type.startswith("application/json"):
                payload = TranscribeBody(**(await request.json()))
                source = path_resolver.resolve_input_file(payload.path)
                return use_case.execute(
                    TranscribeCommand(
                        source_path=source,
                        source_is_temporary=payload.delete_source,
                        model=payload.model,
                        language=payload.language,
                    )
                )

            if not file:
                raise ApplicationError(
                    "Send JSON body with `path` or multipart/form-data with `file`.",
                    status_code=400,
                )

            target = await upload_storage.save_upload(file.filename, await file.read())
            return use_case.execute(
                TranscribeCommand(
                    source_path=target,
                    source_is_temporary=True,
                    model=model,
                    language=language,
                )
            )
        except ApplicationError as err:
            raise HTTPException(status_code=err.status_code, detail=err.message) from err

    return router
