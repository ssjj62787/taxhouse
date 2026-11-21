"""기본 OCR 엔진: Tesseract(pytesseract). 완전 무료·로컬 구동.

사전 준비 (Windows):
  1) https://github.com/UB-Mannheim/tesseract/wiki 에서 설치 (한글 데이터 포함 옵션 체크)
  2) 설치 후 경로를 모른다면 보통 "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
  3) rtax/config.py 의 TESSERACT_CMD 에 그 경로를 넣거나, 환경변수 RTAX_TESSERACT_CMD로 지정
"""
from rtax import config
from rtax.engines.base import OCREngine


class TesseractEngine(OCREngine):
    name = "tesseract"

    def __init__(self):
        import pytesseract
        self._pytesseract = pytesseract
        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

    def recognize(self, image) -> str:
        return self._pytesseract.image_to_string(
            image, lang=config.TESSERACT_LANG, config=config.TESSERACT_CONFIG
        )
