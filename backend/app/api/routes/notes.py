from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.image_processor import preprocess_image
from app.services.ocr_service import extract_text

router = APIRouter()


@router.post("/preprocess-test")
async def test_preprocessing(file: UploadFile = File(...)):
    """Phase 3 — Upload image, get back cleaned version."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()
    result = preprocess_image(image_bytes)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])

    return Response(
        content=result["cleaned_image"],
        media_type="image/png",
        headers={"X-Original-Size": result["original_size"]},
    )


@router.post("/ocr-test")
async def test_ocr(file: UploadFile = File(...)):
    """
    Phase 4 — Upload image of handwritten notes.
    Returns extracted text after preprocessing + OCR.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()

    # Step 1 — Preprocess
    preprocessed = preprocess_image(image_bytes)
    if not preprocessed["success"]:
        raise HTTPException(status_code=422, detail=preprocessed["message"])

    # Step 2 — Extract text
    ocr_result = extract_text(preprocessed["cleaned_image"])

    return {
        "success":      ocr_result["success"],
        "text":         ocr_result["text"],
        "ocr_source":   ocr_result["source"],
        "image_size":   preprocessed["original_size"],
        "char_count":   len(ocr_result["text"]),
        "message":      ocr_result["message"],
    }


@router.get("/")
async def list_notes():
    return {"notes": [], "message": "Notes endpoint ready"}