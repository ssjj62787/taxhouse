"""증빙 폴더(건별) 전체를 읽어 DocumentRecord 리스트로 만듭니다."""
import os
from typing import Callable, List, Optional

from PIL import Image

from rtax import config
from rtax.engines.base import OCREngine, get_engine
from rtax.ingest.document_loader import build_document_record
from rtax.ingest.image_preprocess import preprocess
from rtax.ingest.pdf_input import extract_text_from_pdf
from rtax.models import DocumentRecord

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def load_case_documents(
    case_dir: str,
    engine: Optional[OCREngine] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> List[DocumentRecord]:
    engine = engine or get_engine(config.OCR_ENGINE)
    records: List[DocumentRecord] = []

    for name in sorted(os.listdir(case_dir)):
        path = os.path.join(case_dir, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()

        if progress_cb:
            progress_cb(f"처리 중: {name}")

        if ext == ".pdf":
            raw_text = extract_text_from_pdf(path, engine)
        elif ext in IMAGE_EXTS:
            image = preprocess(Image.open(path))
            raw_text = engine.recognize(image)
        else:
            continue

        records.append(build_document_record(path, raw_text))

    return records
