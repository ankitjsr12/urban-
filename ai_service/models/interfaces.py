from dataclasses import dataclass
from typing import Protocol
@dataclass
class AIResult: label:str; confidence:float; model_name:str; model_version:str; metadata:dict
class Detector(Protocol):
    def detect(self, image: bytes) -> list[AIResult]: ...
class OCRProvider(Protocol):
    def recognize(self, image: bytes) -> tuple[str,float]: ...
class StubDetector:
    def detect(self,image:bytes): return []
class StubOCR:
    def recognize(self,image:bytes): return '',0.0
