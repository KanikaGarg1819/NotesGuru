"""
Image Preprocessing Service
----------------------------
Cleans up phone photos of handwritten notes before sending to OCR.

Steps:
1. Load image
2. Convert to grayscale
3. Deskew (fix tilt)
4. Denoise (remove speckles)
5. Boost contrast (CLAHE)
6. Binarize (black and white threshold)
7. Return cleaned image as bytes
"""

import cv2
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes → OpenCV numpy array."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image — unsupported format or corrupt file.")
    return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def deskew(image: np.ndarray) -> np.ndarray:
    """
    Fix tilt in the image.
    Detects the angle of text lines and rotates to straighten them.
    Works best on images with clear horizontal text.
    """
    # Find all non-zero pixel coordinates
    coords = np.column_stack(np.where(image < 128))  # dark pixels

    if len(coords) < 100:
        # Not enough dark pixels to detect angle — return as is
        return image

    # Get the minimum area rectangle around all dark pixels
    angle = cv2.minAreaRect(coords)[-1]

    # Adjust angle to be in range [-45, 45]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only deskew if tilt is significant (more than 0.5 degrees)
    if abs(angle) < 0.5:
        return image

    # Rotate the image to fix the tilt
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(
        image,
        rotation_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    logger.info(f"Deskewed image by {angle:.2f} degrees")
    return deskewed


def denoise(image: np.ndarray) -> np.ndarray:
    """
    Remove noise and speckles from the image.
    Uses Non-Local Means Denoising — good for scanned/photographed documents.
    h=10: filter strength (higher = more smoothing but may blur text)
    """
    return cv2.fastNlMeansDenoising(image, h=10, templateWindowSize=7, searchWindowSize=21)


def boost_contrast(image: np.ndarray) -> np.ndarray:
    """
    Boost contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    Works better than global histogram equalization for uneven lighting in photos.
    clipLimit=2.0: limits contrast amplification to avoid noise boost
    tileGridSize=(8,8): divides image into 8x8 tiles for local contrast
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)


def binarize(image: np.ndarray) -> np.ndarray:
    """
    Convert to pure black and white using adaptive thresholding.
    Adaptive = threshold varies across the image (handles shadows/uneven lighting).
    Better than simple global threshold for real notebook photos.
    """
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )


def image_to_bytes(image: np.ndarray, format: str = "PNG") -> bytes:
    """Convert OpenCV numpy array back to bytes for storage/transmission."""
    pil_image = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    return buffer.getvalue()


def preprocess_image(image_bytes: bytes) -> dict:
    """
    Full preprocessing pipeline.
    
    Input:  raw image bytes (from upload)
    Output: dict with cleaned image bytes + metadata
    
    Pipeline: load → grayscale → deskew → denoise → contrast → binarize
    """
    try:
        # Step 1 — Load
        image = load_image_from_bytes(image_bytes)
        original_shape = image.shape
        logger.info(f"Loaded image: {original_shape[1]}x{original_shape[0]}px")

        # Step 2 — Grayscale
        gray = convert_to_grayscale(image)

        # Step 3 — Deskew
        deskewed = deskew(gray)

        # Step 4 — Denoise
        denoised = denoise(deskewed)

        # Step 5 — Contrast boost
        contrasted = boost_contrast(denoised)

        # Step 6 — Binarize
        binary = binarize(contrasted)

        # Convert back to bytes
        cleaned_bytes = image_to_bytes(binary)

        return {
            "success": True,
            "cleaned_image": cleaned_bytes,
            "original_size": f"{original_shape[1]}x{original_shape[0]}",
            "message": "Image preprocessed successfully",
        }

    except ValueError as e:
        logger.error(f"Image preprocessing failed: {e}")
        return {
            "success": False,
            "cleaned_image": None,
            "original_size": None,
            "message": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        return {
            "success": False,
            "cleaned_image": None,
            "original_size": None,
            "message": "Preprocessing failed — unexpected error",
        }