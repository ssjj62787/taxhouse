"""PDF 한 파일에서 텍스트를 뽑아냅니다.

전자 PDF(글자가 선택되는 파일)는 PyMuPDF로 바로 텍스트를 추출하고,
스캔 PDF(이미지로만 된 페이지)는 페이지를 이미지로 렌더링한 뒤 OCR 엔진에 넘깁니다.
(PyMuPDF 하나로 텍스트 추출/이미지 렌더링을 모두 처리해서 의존성을 줄였습니다 —
pdfplumber가 끌어오는 cryptography는 환경에 따라 Rust 빌드가 필요해 설치가 깨지기 쉽습니다.)
"""
import fitz  # PyMuPDF
from PIL import Image

from rtax import config
from rtax.engines.base import OCREngine
from rtax.ingest.image_preprocess import preprocess


def extract_text_from_pdf(path: str, engine: OCREngine) -> str:
    doc = fitz.open(path)
    pages_text = []
    for i in range(len(doc)):
        text = doc[i].get_text() or ""
        if len(text.strip()) >= config.SCANNED_PAGE_TEXT_THRESHOLD:
            pages_text.append(text)
        else:
            pages_text.append(_ocr_page(doc, i, engine))
    return "\n".join(pages_text)


def _ocr_page(doc: "fitz.Document", page_index: int, engine: OCREngine) -> str:
    page = doc[page_index]
    zoom = config.OCR_RENDER_DPI / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    image = preprocess(image)
    return engine.recognize(image)
