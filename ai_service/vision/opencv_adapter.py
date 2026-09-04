import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class OpenCVAdapter:
    """Adapter for OpenCV operations."""
    
    @staticmethod
    def decode_image(image_bytes: bytes) -> tuple[np.ndarray | None, dict]:
        """Decodes raw image bytes into an OpenCV numpy array."""
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return None, {}
            h, w = img.shape[:2]
            return img, {"height": h, "width": w}
        except Exception as e:
            logger.error(f"Error decoding image: {e}")
            return None, {}

    @staticmethod
    def encode_image(img: np.ndarray, format: str = ".jpg") -> bytes | None:
        """Encodes an OpenCV image to bytes."""
        try:
            success, encoded = cv2.imencode(format, img)
            if success:
                return encoded.tobytes()
            return None
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            return None

    @staticmethod
    def crop_image(img: np.ndarray, bbox: dict) -> np.ndarray | None:
        """Crops an image given a normalized bounding box (x_min, y_min, x_max, y_max)."""
        try:
            h, w = img.shape[:2]
            x_min = int(bbox.get("x_min", 0) * w)
            y_min = int(bbox.get("y_min", 0) * h)
            x_max = int(bbox.get("x_max", 1.0) * w)
            y_max = int(bbox.get("y_max", 1.0) * h)
            
            # Ensure within bounds
            x_min = max(0, min(x_min, w - 1))
            y_min = max(0, min(y_min, h - 1))
            x_max = max(x_min + 1, min(x_max, w))
            y_max = max(y_min + 1, min(y_max, h))
            
            return img[y_min:y_max, x_min:x_max]
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            return None

    @staticmethod
    def preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
        """Preprocesses image for better OCR results."""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Bilateral filter removes noise while keeping edges sharp
            filtered = cv2.bilateralFilter(gray, 11, 17, 17)
            # Contrast Limited Adaptive Histogram Equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(filtered)
            # Convert back to BGR for PaddleOCR which expects 3 channels usually
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            return enhanced_bgr
        except Exception as e:
            logger.error(f"Error preprocessing for OCR: {e}")
            return img
