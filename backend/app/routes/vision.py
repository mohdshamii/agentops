from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.vision_service import global_vision_service
from app.schemas import VisionAnalysisRequest

router = APIRouter(prefix="/api/vision", tags=["vision"])

@router.post("/analyze")
async def analyze_image(request: VisionAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze image using Hugging Face Vision model (BLIP)
    with base64 or URL inputs.
    """
    if not request.image_base64 and not request.image_url:
        raise HTTPException(status_code=400, detail="Must provide either image_base64 or image_url")

    result = global_vision_service.analyze_image(
        image_base64=request.image_base64,
        image_url=request.image_url,
        prompt=request.prompt or "Describe this image"
    )
    return result
