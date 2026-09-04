import math
import uuid
from datetime import datetime, timezone
from ai_service.models.interfaces import AIResult, Tracker


class TrackedObject:
    def __init__(self, tracking_id: str, label: str, bbox: dict[str, float], confidence: float, frame_id: int):
        self.tracking_id = tracking_id
        self.label = label
        self.bbox = bbox
        self.confidence = confidence
        self.last_frame = frame_id
        self.hits = 1
        self.age = 1


class ByteTrackSpatialTracker(Tracker):
    """Spatial-temporal multi-object tracker associating detections across video frames."""

    def __init__(self, max_distance: float = 0.25, max_age: int = 30):
        self.max_distance = max_distance
        self.max_age = max_age
        self.tracks: list[TrackedObject] = []
        self.frame_counter = 0

    def _iou_distance(self, bbox1: dict[str, float], bbox2: dict[str, float]) -> float:
        # Compute centroid distance between normalized bounding boxes
        c1_x = (bbox1["x_min"] + bbox1["x_max"]) / 2
        c1_y = (bbox1["y_min"] + bbox1["y_max"]) / 2
        c2_x = (bbox2["x_min"] + bbox2["x_max"]) / 2
        c2_y = (bbox2["y_min"] + bbox2["y_max"]) / 2
        return math.hypot(c1_x - c2_x, c1_y - c2_y)

    def track(self, detections: list[AIResult], frame_id: int | None = None) -> list[AIResult]:
        self.frame_counter = frame_id if frame_id is not None else (self.frame_counter + 1)
        matched_track_indices = set()
        results: list[AIResult] = []

        for det in detections:
            if not det.bounding_box:
                det.tracking_id = f"TRK-{uuid.uuid4().hex[:8].upper()}"
                results.append(det)
                continue

            best_match_idx = None
            best_dist = float("inf")

            for idx, track in enumerate(self.tracks):
                if idx in matched_track_indices or track.label != det.label:
                    continue
                dist = self._iou_distance(det.bounding_box, track.bbox)
                if dist < self.max_distance and dist < best_dist:
                    best_dist = dist
                    best_match_idx = idx

            if best_match_idx is not None:
                track = self.tracks[best_match_idx]
                track.bbox = det.bounding_box
                track.confidence = det.confidence
                track.last_frame = self.frame_counter
                track.hits += 1
                det.tracking_id = track.tracking_id
                matched_track_indices.add(best_match_idx)
            else:
                new_id = f"TRK-{uuid.uuid4().hex[:8].upper()}"
                new_track = TrackedObject(
                    tracking_id=new_id,
                    label=det.label,
                    bbox=det.bounding_box,
                    confidence=det.confidence,
                    frame_id=self.frame_counter,
                )
                self.tracks.append(new_track)
                det.tracking_id = new_id

            results.append(det)

        # Purge stale tracks
        self.tracks = [t for t in self.tracks if (self.frame_counter - t.last_frame) <= self.max_age]
        return results
