from dataclasses import dataclass, field
from typing import Protocol, Any


@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass
class AIResult:
    label: str
    confidence: float
    model_name: str
    model_version: str
    bounding_box: dict[str, float] | None = None
    tracking_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OCRResult:
    plate_number: str
    ocr_confidence: float
    verification_status: str
    model_name: str
    model_version: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Detector(Protocol):
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.4) -> list[AIResult]: ...


class Tracker(Protocol):
    def track(self, detections: list[AIResult], frame_id: int | None = None) -> list[AIResult]: ...


class OCRProvider(Protocol):
    def recognize(self, image_bytes: bytes) -> tuple[str, float]: ...


class StubDetector:
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.4) -> list[AIResult]:
        return []


class StubOCR:
    def recognize(self, image_bytes: bytes) -> tuple[str, float]:
        return '', 0.0
