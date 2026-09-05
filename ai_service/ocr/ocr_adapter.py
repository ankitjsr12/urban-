import os
import sys
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Add PaddleOCR directory to sys.path if custom clone exists
PADDLEOCR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'PaddleOCR'))
if os.path.exists(PADDLEOCR_DIR) and PADDLEOCR_DIR not in sys.path:
    sys.path.insert(0, PADDLEOCR_DIR)

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
            # Initialize PaddleOCR with backward/forward compatibility for arguments across versions
            try:
                self.ocr = PaddleOCR(use_textline_orientation=True, lang='en')
            except TypeError:
                try:
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                except TypeError:
                    self.ocr = PaddleOCR(lang='en')
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
            try:
                result = self.ocr.ocr(img, cls=True)
            except (TypeError, ValueError):
                result = self.ocr.ocr(img)

            if not result or not result[0]:
                return "", 0.0

            best_text = ""
            best_conf = 0.0
            first = result[0]

            if isinstance(first, dict):
                rec_texts = first.get("rec_texts", [])
                rec_scores = first.get("rec_scores", [])
                for text, conf in zip(rec_texts, rec_scores):
                    if conf > best_conf:
                        best_conf = float(conf)
                        best_text = str(text)
                return best_text, best_conf

            # result[0] contains the boxes, text and confidence
            for line in first:
                if not line:
                    continue
                coords, (text, confidence) = line
                if confidence > best_conf:
                    best_conf = float(confidence)
                    best_text = str(text)

            return best_text, best_conf
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            return "", 0.0
