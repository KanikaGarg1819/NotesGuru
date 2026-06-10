from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.image_processor import preprocess_image

router = APIRouter()


@router.post("/preprocess-test")
async def test_preprocessing(file: UploadFile = File(...)):
    """
    TEST ENDPOINT — Phase 3
    Upload any image of handwritten notes and get back the cleaned version.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()
    result = preprocess_image(image_bytes)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])

    return Response(
        content=result["cleaned_image"],
        media_type="image/png",
        headers={
            "X-Original-Size": result["original_size"],
            "X-Message": result["message"],
        },
    )


@router.get("/")
async def list_notes():
    return {"notes": [], "message": "Notes endpoint ready"}