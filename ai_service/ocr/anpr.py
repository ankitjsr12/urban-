import re
import cv2
import numpy as np
import logging
from ai_service.models.interfaces import OCRProvider
from ai_service.ocr.ocr_adapter import OCRAdapter

logger = logging.getLogger(__name__)

# License plate pattern (standard international & Indian formats)
PLATE_REGEX = re.compile(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}|[A-Z0-9]{6,10}")


class ANPROCRService(OCRProvider):
    """Automatic Number Plate Recognition (ANPR) and OCR pipeline."""

    def __init__(self, model_name: str = "urbansense-anpr-ocr", model_version: str = "1.0.0"):
        self.model_name = model_name
        self.model_version = model_version
        self.ocr_adapter = OCRAdapter()

    def preprocess_image(self, image_bytes: bytes) -> tuple[np.ndarray | None, dict]:
        """Preprocesses raw image buffer with grayscale, bilateral filtering, and edge contrast enhancement."""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return None, {}

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Bilateral filter removes noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        # Contrast Limited Adaptive Histogram Equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(filtered)

        return enhanced, {"height": h, "width": w}

    def recognize(self, image_bytes: bytes) -> tuple[str, float]:
        """Extracts text, locates plate characters, and returns (plate_number, confidence)."""
        if not image_bytes:
            return "", 0.0

        preprocessed, meta = self.preprocess_image(image_bytes)
        if preprocessed is None:
            return "", 0.0

        np_arr = np.frombuffer(image_bytes, np.uint8)
        raw_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Heuristic plate feature localization (rectangular character band extraction)
        edged = cv2.Canny(preprocessed, 30, 200)
        contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        plate_text = ""
        confidence = 0.0

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h) if h > 0 else 0
                if 2.0 <= aspect_ratio <= 5.5 and raw_img is not None:
                    plate_crop = raw_img[y:y+h, x:x+w]
                    if plate_crop.size > 0:
                        text, conf = self.ocr_adapter.extract_text(plate_crop)
                        cleaned = "".join(ch for ch in text.upper() if ch.isalnum())
                        if cleaned and PLATE_REGEX.search(cleaned):
                            plate_text = cleaned
                            confidence = conf
                            break
                        elif conf > confidence and cleaned:
                            plate_text = cleaned
                            confidence = conf

        # Fallback: run OCR on full image if no candidate contour produced high confidence
        if not plate_text and raw_img is not None:
            text, conf = self.ocr_adapter.extract_text(raw_img)
            cleaned = "".join(ch for ch in text.upper() if ch.isalnum())
            if cleaned:
                plate_text = cleaned
                confidence = conf

        return plate_text, round(confidence, 4)
