import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

class OCRAdapter:
    """Adapter for PaddleOCR operations."""
    
    def __init__(self):
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        if os.environ.get("OCR_ENABLED", "true").lower() != "true":
            logger.info("OCR is disabled via OCR_ENABLED.")
            return

        try:
            from paddleocr import PaddleOCR
            # Initialize PaddleOCR.
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("PaddleOCR initialized successfully.")
        except ImportError:
            logger.warning("PaddleOCR package not found. OCR will not function.")
        except Exception as e:
            logger.error(f"Error initializing PaddleOCR: {e}")

    def extract_text(self, img: np.ndarray) -> tuple[str, float]:
        """Extracts text from an OpenCV image."""
        if self.ocr is None:
            return "", 0.0

        try:
            result = self.ocr.ocr(img, cls=True)
            if not result or not result[0]:
                return "", 0.0

            best_text = ""
            best_conf = 0.0
            
            # result[0] contains the boxes, text and confidence
            for line in result[0]:
                if not line:
                    continue
                coords, (text, confidence) = line
                if confidence > best_conf:
                    best_conf = confidence
                    best_text = text

            return best_text, best_conf
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            return "", 0.0
