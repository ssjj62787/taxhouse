"""OCR 엔진 공용 인터페이스. 새 엔진을 추가하려면 이 클래스를 상속해서
recognize()만 구현하면 ingest 쪽 코드를 바꾸지 않고 교체할 수 있습니다.
"""
from abc import ABC, abstractmethod


class OCREngine(ABC):
    name: str = "base"

    @abstractmethod
    def recognize(self, image) -> str:
        """PIL.Image 한 장을 받아 인식된 텍스트를 반환."""
        raise NotImplementedError


def get_engine(name: str) -> OCREngine:
    if name == "tesseract":
        from rtax.engines.tesseract_engine import TesseractEngine
        return TesseractEngine()
    if name == "claude":
        from rtax.engines.claude_engine import ClaudeVisionEngine
        return ClaudeVisionEngine()
    raise ValueError(f"알 수 없는 OCR_ENGINE 설정: {name}")
