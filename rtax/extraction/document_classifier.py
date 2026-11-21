"""문서 텍스트의 키워드로 증빙 종류를 분류."""
from rtax.models import DocType

_RULES = [
    (DocType.AUCTION_PAYMENT_CERT, ["경락대금완납증명원", "경락대금"]),
    (DocType.NOTARY_RECEIPT, ["법무사"]),
    (DocType.BROKER_RECEIPT, ["공인중개사", "중개보수", "부동산중개"]),
    (DocType.SALES_CONTRACT, ["매매계약서", "부동산매매계약서"]),
]


def classify(text: str) -> DocType:
    for doc_type, keywords in _RULES:
        if any(kw in text for kw in keywords):
            return doc_type
    return DocType.UNKNOWN
