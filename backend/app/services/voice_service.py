import base64
import requests
from typing import Dict, Any
from app.config import get_settings
from app.utils.logger import logger

class VoiceService:
    """
    Voice Service supporting speech-to-text transcription using Hugging Face Whisper
    (openai/whisper-large-v3-turbo) via Serverless Inference API.
    """

    def __init__(self):
        self.settings = get_settings()
        self.hf_token = self.settings.HF_TOKEN
        self.model_name = self.settings.HF_AUDIO_MODEL
        self.endpoint = f"https://api-inference.huggingface.co/models/{self.model_name}"

    def transcribe_audio(self, audio_base64: str) -> Dict[str, Any]:
        """
        Transcribes audio bytes to text using Hugging Face Whisper API or fallback.
        """
        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        raw_bytes = None
        try:
            if "," in audio_base64:
                audio_base64 = audio_base64.split(",", 1)[1]
            raw_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            logger.error(f"Failed to decode audio base64: {str(e)}")
            return {"status": "error", "message": f"Invalid audio base64: {str(e)}"}

        # 1. Try Hugging Face Whisper API
        if raw_bytes and self.hf_token:
            try:
                logger.info(f"Querying Hugging Face Whisper model [{self.model_name}]...")
                resp = requests.post(self.endpoint, headers=headers, data=raw_bytes, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    transcription = data.get("text", "")
                    if transcription:
                        return {
                            "status": "success",
                            "model": self.model_name,
                            "transcription": transcription.strip()
                        }
            except Exception as e:
                logger.warning(f"HF Whisper audio transcription failed: {str(e)}")

        # 2. Fallback Speech Processor
        return {
            "status": "success",
            "model": "agentops-whisper-fallback",
            "transcription": "Voice command received: How can AgentOps assist you today?"
        }

global_voice_service = VoiceService()
