"""PDF 한 파일에서 텍스트를 뽑아냅니다.

전자 PDF(글자가 선택되는 파일)는 pdfplumber로 바로 텍스트를 추출하고,
스캔 PDF(이미지로만 된 페이지)는 페이지를 이미지로 렌더링한 뒤 OCR 엔진에 넘깁니다.
"""
from rtax import config
from rtax.engines.base import OCREngine
from rtax.ingest.image_preprocess import preprocess


def extract_text_from_pdf(path: str, engine: OCREngine) -> str:
    import pdfplumber

    pages_text = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if len(text.strip()) >= config.SCANNED_PAGE_TEXT_THRESHOLD:
                pages_text.append(text)
            else:
                pages_text.append(_ocr_page(path, i, engine))
    return "\n".join(pages_text)


def _ocr_page(path: str, page_index: int, engine: OCREngine) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(path)
    page = doc[page_index]
    zoom = config.OCR_RENDER_DPI / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    from PIL import Image
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    image = preprocess(image)
    return engine.recognize(image)
