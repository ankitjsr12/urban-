"""OpenCV integration module for UrbanSense.

Provides a unified interface for OpenCV operations across the project,
reusing the existing OpenCVAdapter from ai_service.vision.opencv_adapter.
"""

import logging

logger = logging.getLogger(__name__)

try:
    import cv2
except ImportError as err:
    logger.warning("OpenCV (cv2) is not available: %s", err)
    cv2 = None

try:
    from ai_service.vision.opencv_adapter import OpenCVAdapter
except ImportError as err:
    logger.warning("OpenCVAdapter could not be imported: %s", err)
    OpenCVAdapter = None

__all__ = ["OpenCVAdapter", "cv2"]
