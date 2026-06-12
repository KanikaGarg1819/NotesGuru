"""
OCR Service
-----------
Extracts text from preprocessed images of handwritten notes.

Primary:  Google Cloud Vision API (best for handwriting)
Fallback: Tesseract (free, runs locally)

Always call preprocess_image() before calling extract_text().
"""

import os
import io
import logging
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


# ── Google Vision ─────────────────────────────────────────────────

def extract_text_google_vision(image_bytes: bytes) -> dict:
    """
    Extract text from image using Google Cloud Vision API.
    Uses DOCUMENT_TEXT_DETECTION which is optimized for dense text like notes.
    """
    try:
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()
        image  = vision.Image(content=image_bytes)

        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")

        full_text = response.full_text_annotation.text

        if not full_text:
            return {
                "success": False,
                "text": "",
                "source": "google_vision",
                "message": "No text detected in image",
            }

        # Clean up the extracted text
        cleaned = clean_extracted_text(full_text)

        logger.info(f"Google Vision extracted {len(cleaned)} characters")
        return {
            "success": True,
            "text": cleaned,
            "raw_text": full_text,
            "source": "google_vision",
            "message": "Text extracted successfully",
        }

    except ImportError:
        logger.error("google-cloud-vision not installed")
        return {
            "success": False,
            "text": "",
            "source": "google_vision",
            "message": "google-cloud-vision package not available",
        }
    except Exception as e:
        logger.error(f"Google Vision failed: {e}")
        return {
            "success": False,
            "text": "",
            "source": "google_vision",
            "message": str(e),
        }


# ── Tesseract Fallback ────────────────────────────────────────────

def extract_text_tesseract(image_bytes: bytes) -> dict:
    """
    Extract text using Tesseract OCR (local, free fallback).
    Less accurate than Google Vision for handwriting but always available.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # PSM 6 = assume a single uniform block of text (good for notes)
        config = "--psm 6 --oem 3"
        raw_text = pytesseract.image_to_string(image, config=config)

        if not raw_text.strip():
            return {
                "success": False,
                "text": "",
                "source": "tesseract",
                "message": "No text detected in image",
            }

        cleaned = clean_extracted_text(raw_text)

        logger.info(f"Tesseract extracted {len(cleaned)} characters")
        return {
            "success": True,
            "text": cleaned,
            "raw_text": raw_text,
            "source": "tesseract",
            "message": "Text extracted via Tesseract fallback",
        }

    except Exception as e:
        logger.error(f"Tesseract failed: {e}")
        return {
            "success": False,
            "text": "",
            "source": "tesseract",
            "message": str(e),
        }


# ── Text Cleanup ──────────────────────────────────────────────────

def clean_extracted_text(text: str) -> str:
    """
    Clean up raw OCR output.
    - Remove excessive blank lines
    - Strip leading/trailing whitespace per line
    - Remove lines that are just symbols/noise
    """
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Skip empty lines and noise lines (less than 2 real characters)
        real_chars = sum(1 for c in line if c.isalnum())
        if real_chars < 2:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ── Main Entry Point ──────────────────────────────────────────────

def extract_text(image_bytes: bytes) -> dict:
    """
    Extract text from image bytes.

    Tries Google Vision first — falls back to Tesseract if:
    - Credentials not found
    - API call fails
    - No text detected

    Input:  cleaned image bytes (output of preprocess_image)
    Output: dict with extracted text + metadata
    """
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    google_available = bool(credentials_path and os.path.exists(credentials_path))

    if google_available:
        logger.info("Using Google Cloud Vision API")
        result = extract_text_google_vision(image_bytes)

        if result["success"]:
            return result

        # Google failed — fall back to Tesseract
        logger.warning(f"Google Vision failed: {result['message']} — falling back to Tesseract")

    else:
        logger.warning("Google credentials not found — using Tesseract fallback")

    return extract_text_tesseract(image_bytes)