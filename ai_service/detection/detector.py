import os
import sys
import logging
from ai_service.models.interfaces import AIResult, Detector
from ai_service.vision.opencv_adapter import OpenCVAdapter

logger = logging.getLogger(__name__)

# Add YOLO/YOLO to path if we want to import ultralytics from it
YOLO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'YOLO', 'YOLO'))
if os.path.exists(YOLO_DIR):
    sys.path.insert(0, YOLO_DIR)

class EdgeUrbanDetector(Detector):
    """YOLO-based urban hazard, object, and infrastructure detector."""

    def __init__(self, model_name: str = "urbansense-yolo", model_version: str = "1.0.0"):
        self.model_name = model_name
        self.model_version = model_version
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            model_path = os.environ.get("YOLO_MODEL_PATH", "")
            if not model_path or not os.path.exists(model_path):
                default_candidate = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..', '..', 'YOLO', 'models', 'yolov8n.pt')
                )
                if os.path.exists(default_candidate):
                    model_path = default_candidate
                else:
                    logger.warning(
                        "Existing YOLO implementation found, but no model weights are available on disk. "
                        "Set YOLO_MODEL_PATH to a valid model weights file (.pt/.onnx)."
                    )
                    self.model = None
                    return
            
            # Use MPS on Apple Silicon if available, otherwise CPU/CUDA
            self.model = YOLO(model_path)
            logger.info(f"Loaded YOLO model from {model_path}")
        except ImportError:
            logger.error("ultralytics package not found or YOLO folder missing. YOLO detection will not function.")
        except Exception as e:
            logger.error(f"Could not load YOLO model: {e}")

    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.4) -> list[AIResult]:
        if not image_bytes or self.model is None:
            return []

        # Decode image using adapter
        img, meta = OpenCVAdapter.decode_image(image_bytes)
        if img is None:
            return []

        results: list[AIResult] = []

        try:
            # Run inference
            inference_results = self.model(img, conf=confidence_threshold, verbose=False)
            
            for r in inference_results:
                boxes = r.boxes
                for box in boxes:
                    # Convert to normalized coordinates (0.0 to 1.0)
                    xyxyn = box.xyxyn[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    cls_name = self.model.names[cls_id].upper() if self.model.names else str(cls_id)
                    
                    results.append(
                        AIResult(
                            label=cls_name,
                            confidence=round(conf, 4),
                            model_name=self.model_name,
                            model_version=self.model_version,
                            bounding_box={
                                "x_min": round(float(xyxyn[0]), 4),
                                "y_min": round(float(xyxyn[1]), 4),
                                "x_max": round(float(xyxyn[2]), 4),
                                "y_max": round(float(xyxyn[3]), 4),
                            },
                            metadata={"image_height": meta.get("height"), "image_width": meta.get("width")},
                        )
                    )
        except Exception as e:
            logger.error(f"Error during YOLO inference: {e}")

        return results
