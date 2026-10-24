from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.voice_service import global_voice_service
from app.schemas import VoiceTranscriptionRequest

router = APIRouter(prefix="/api/voice", tags=["voice"])

@router.post("/transcribe")
async def transcribe_audio(request: VoiceTranscriptionRequest) -> Dict[str, Any]:
    """
    Transcribe audio base64 payload to text using Hugging Face Whisper model
    """
    if not request.audio_base64:
        raise HTTPException(status_code=400, detail="audio_base64 is required")

    result = global_voice_service.transcribe_audio(request.audio_base64)
    return result
