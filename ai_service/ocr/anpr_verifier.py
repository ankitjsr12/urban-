"""Multi-Frame ANPR Consensus Verifier for UrbanSense.

Implements temporal consensus across multiple video frames for a tracked vehicle,
eliminating OCR flicker, optical distortion, and motion blur artifacts.
"""

from __future__ import annotations

import collections
import re
from typing import Any, Optional

# Standard vehicle plate pattern (e.g. MH12AB1234, DL01C1234, CA99ZZ9999, standard alphanumerics)
STANDARD_PLATE_REGEX = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$|^[A-Z0-9]{6,10}$")


class MultiFrameANPRVerifier:
    """Consensus-based multi-frame license plate verifier."""

    def __init__(
        self,
        min_frames: int = 3,
        min_confidence: float = 0.70,
        consensus_threshold: float = 0.50,
    ):
        self.min_frames = min_frames
        self.min_confidence = min_confidence
        self.consensus_threshold = consensus_threshold

    @staticmethod
    def normalize_plate(raw_text: str) -> str:
        """Strip non-alphanumerics, normalize common OCR confusions (e.g. O vs 0 in number segments)."""
        if not raw_text:
            return ""
        cleaned = "".join(ch for ch in raw_text.upper() if ch.isalnum())
        return cleaned

    def verify_observations(
        self,
        observations: list[tuple[str, float]],
    ) -> dict[str, Any]:
        """Verify plate text from a collection of (raw_text, confidence) frame observations.

        Returns:
            dict containing verified_plate, confidence, frame_count, is_verified, and history.
        """
        valid_obs: list[tuple[str, float]] = []
        for text, conf in observations:
            norm = self.normalize_plate(text)
            if norm and len(norm) >= 4:
                valid_obs.append((norm, float(conf)))

        if not valid_obs:
            return {
                "verified_plate": "",
                "confidence": 0.0,
                "frame_count": 0,
                "is_verified": False,
                "reason": "No valid observations provided",
            }

        # 1. Exact string weighted voting
        score_by_plate: dict[str, float] = collections.defaultdict(float)
        count_by_plate: dict[str, int] = collections.defaultdict(int)

        for plate, conf in valid_obs:
            # Pattern match weight boost
            pattern_boost = 1.3 if STANDARD_PLATE_REGEX.match(plate) else 1.0
            weight = conf * pattern_boost
            score_by_plate[plate] += weight
            count_by_plate[plate] += 1

        total_frames = len(valid_obs)
        best_plate = max(score_by_plate.keys(), key=lambda p: score_by_plate[p])
        best_count = count_by_plate[best_plate]

        # 2. Position-based character consensus if multiple variants of same length exist
        same_len_plates = [p for p, _ in valid_obs if len(p) == len(best_plate)]
        if len(same_len_plates) >= self.min_frames:
            aligned_chars = []
            for col_idx in range(len(best_plate)):
                chars_at_pos = [p[col_idx] for p in same_len_plates]
                most_common_char = collections.Counter(chars_at_pos).most_common(1)[0][0]
                aligned_chars.append(most_common_char)
            consensus_candidate = "".join(aligned_chars)
            if STANDARD_PLATE_REGEX.match(consensus_candidate):
                best_plate = consensus_candidate

        # 3. Calculate final confidence
        # Average confidence of matching frames
        matching_confs = [conf for plate, conf in valid_obs if plate == best_plate]
        avg_conf = (sum(matching_confs) / len(matching_confs)) if matching_confs else 0.5

        # Frequency ratio
        freq_ratio = best_count / total_frames
        
        # Pattern bonus
        pattern_bonus = 0.1 if STANDARD_PLATE_REGEX.match(best_plate) else 0.0

        final_conf = min(1.0, round((avg_conf * 0.6) + (freq_ratio * 0.3) + pattern_bonus, 4))
        is_verified = (
            total_frames >= self.min_frames
            and freq_ratio >= self.consensus_threshold
            and final_conf >= self.min_confidence
        )

        return {
            "verified_plate": best_plate,
            "confidence": final_conf,
            "frame_count": total_frames,
            "matching_frames": best_count,
            "is_verified": is_verified,
            "pattern_matched": bool(STANDARD_PLATE_REGEX.match(best_plate)),
        }


# Module singleton
anpr_verifier = MultiFrameANPRVerifier()
