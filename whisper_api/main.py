from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile

from whisper_api.core.schemas import TranscribeBody
from whisper_api.core.settings import Settings
from whisper_api.services.speech_service import SpeechService

settings = Settings.from_env()
speech_service = SpeechService(settings)
app = FastAPI(title="Whisper API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(
    request: Request,
    file: UploadFile | None = File(default=None),
    model: str = Form(default="turbo"),
    language: str | None = Form(default=None),
    task: str = Form(default="transcribe"),
    save_txt: bool = Form(default=False),
    save_json: bool = Form(default=False),
    delete_source: bool = Form(default=False),
    diarize: bool = Form(default=False),
    min_speakers: int | None = Form(default=None),
    max_speakers: int | None = Form(default=None),
):
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("application/json"):
        payload = TranscribeBody(**(await request.json()))
        source = speech_service.resolve_relative_source(payload.path)
        return speech_service.transcribe(
            source_path=source,
            model_name=payload.model,
            language=payload.language,
            task=payload.task,
            save_txt=payload.save_txt,
            save_json=payload.save_json,
            delete_source=payload.delete_source,
            diarize=payload.diarize,
            min_speakers=payload.min_speakers,
            max_speakers=payload.max_speakers,
        )

    if not file:
        raise HTTPException(
            status_code=400,
            detail="Send JSON body with `path` or multipart/form-data with `file`.",
        )

    source = speech_service.save_upload(file.filename, await file.read())
    return speech_service.transcribe(
        source_path=source,
        model_name=model,
        language=language,
        task=task,
        save_txt=save_txt,
        save_json=save_json,
        delete_source=True,
        diarize=diarize,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

