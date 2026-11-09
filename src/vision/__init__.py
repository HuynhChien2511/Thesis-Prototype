"""
Module Thị giác Máy tính (Computer Vision) cho Robot Trợ lý AI.
Bao gồm:
  - VideoCaptureThread: Luồng đọc camera thời gian thực không độ trễ.
  - ObjectDetector: Bộ nhận diện đối tượng thời gian thực sử dụng YOLOv8.
  - VisionContextManager: Quản lý ngữ cảnh thị giác và chụp ảnh cho Multimodal LLM.
"""

from .camera import VideoCaptureThread
from .detector import ObjectDetector, DetectionResult
from .tracker import PersonTracker, TrackedPerson
from .visual_context import VisionContextManager

__all__ = [
    "VideoCaptureThread",
    "ObjectDetector",
    "DetectionResult",
    "PersonTracker",
    "TrackedPerson",
    "VisionContextManager"
]
