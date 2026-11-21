"""라벨 기반 항목 추출.

핵심 원칙: 문서를 통째로 긁어서 숫자/날짜를 아무거나 집는 게 아니라,
'라벨 단어' 주변의 값만 그 라벨에 매칭합니다. 매칭 실패시 None을 반환하고,
호출부(case_builder)가 [미확인/누락]으로 표시하도록 합니다.
"""
import re
from typing import List, Optional, Tuple

from rtax.extraction.korean_number import parse_korean_amount
from rtax.models import Evidence, ExtractedField

_DATE_PATTERNS = [
    re.compile(r"(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})일?"),
]

_AMOUNT_WINDOW = 60     # 라벨 뒤 몇 글자까지를 금액 탐색 범위로 볼지
_DATE_WINDOW = 40


def _normalize_date(y, m, d) -> str:
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def find_label_positions(text: str, labels: List[str]) -> List[Tuple[int, str]]:
    positions = []
    for label in labels:
        for m in re.finditer(re.escape(label), text):
            positions.append((m.end(), label))
    return positions


def extract_date_near_label(
    text: str, labels: List[str], source_file: str, field_label: str
) -> ExtractedField:
    positions = find_label_positions(text, labels)
    for pos, matched_label in positions:
        window = text[pos: pos + _DATE_WINDOW]
        for pat in _DATE_PATTERNS:
            m = pat.search(window)
            if m:
                value = _normalize_date(*m.groups())
                snippet = text[max(0, pos - len(matched_label)): pos + _DATE_WINDOW]
                return ExtractedField(
                    label=field_label,
                    value=value,
                    confidence="확인",
                    evidence=Evidence(source_file=source_file, snippet=snippet.strip()),
                )
    return ExtractedField(
        label=field_label, value=None, confidence="미확인/누락",
        note=f"라벨({'/'.join(labels)}) 주변에서 날짜 패턴을 찾지 못함",
    )


def extract_amount_near_label(
    text: str, labels: List[str], source_file: str, field_label: str
) -> ExtractedField:
    positions = find_label_positions(text, labels)
    for pos, matched_label in positions:
        window = text[pos: pos + _AMOUNT_WINDOW]
        amount = parse_korean_amount(window)
        if amount is not None:
            snippet = text[max(0, pos - len(matched_label)): pos + _AMOUNT_WINDOW]
            return ExtractedField(
                label=field_label,
                value=amount,
                confidence="확인",
                evidence=Evidence(source_file=source_file, snippet=snippet.strip()),
            )
    return ExtractedField(
        label=field_label, value=None, confidence="미확인/누락",
        note=f"라벨({'/'.join(labels)}) 주변에서 금액을 인식하지 못함 — 원문 재확인 필요",
    )


_ADDR_PATTERN = re.compile(
    r"([가-힣]+(?:특별시|광역시|도)[ \t]*[가-힣0-9]+(?:시|군|구)[ \t]*[가-힣0-9]+(?:읍|면|동|로|길)[가-힣0-9\- \t]*)"
)


def extract_address(text: str, source_file: str) -> ExtractedField:
    m = _ADDR_PATTERN.search(text)
    if m:
        value = re.sub(r"\s+", " ", m.group(1)).strip()
        return ExtractedField(
            label="소재지", value=value, confidence="확인",
            evidence=Evidence(source_file=source_file, snippet=value),
        )
    return ExtractedField(
        label="소재지", value=None, confidence="미확인/누락",
        note="주소 패턴(시/도 + 시/군/구 + 동/로/길)을 찾지 못함",
    )


_AREA_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(㎡|m2|m²|평)")
_AREA_LABELS = ["전용면적", "대지면적", "공급면적", "면적"]


def extract_area(text: str, source_file: str) -> ExtractedField:
    for label in _AREA_LABELS:
        idx = text.find(label)
        if idx == -1:
            continue
        window = text[idx: idx + 30]
        m = _AREA_PATTERN.search(window)
        if m:
            value = f"{m.group(1)}{m.group(2)} ({label})"
            return ExtractedField(
                label="면적", value=value, confidence="확인",
                evidence=Evidence(source_file=source_file, snippet=window.strip()),
            )
    return ExtractedField(
        label="면적", value=None, confidence="미확인/누락",
        note="면적 라벨(전용/대지/공급/면적) 및 단위(㎡·평)를 함께 찾지 못함",
    )


_PROPERTY_TYPE_KEYWORDS = {
    "집합건물": ["아파트", "오피스텔", "집합건물", "전용면적"],
    "건물": ["건물", "단독주택", "근린생활시설"],
    "토지": ["토지", "대지", "임야", "전", "답"],
}


_NOTARY_ITEM_LABELS = [
    "취득세", "지방교육세", "농어촌특별세", "인지세",
    "등기신청수수료", "국민주택채권", "채권매입", "법무사보수",
]


def extract_notary_items(text: str, source_file: str) -> List[ExtractedField]:
    """법무사영수증 한 건에서 항목별 금액을 뽑아 리스트로 반환.

    같은 라벨이 중복 매칭되지 않도록 먼저 나온 라벨을 우선 사용.
    """
    items: List[ExtractedField] = []
    seen = set()
    for label in _NOTARY_ITEM_LABELS:
        if label in seen:
            continue
        field_ = extract_amount_near_label(text, [label], source_file, label)
        if field_.value is not None:
            items.append(field_)
            seen.add(label)
    if not items:
        items.append(ExtractedField(
            label="법무사영수증 항목", value=None, confidence="미확인/누락",
            note="취득세/인지세/등기신청수수료/법무사보수 등 항목 라벨을 하나도 찾지 못함",
        ))
    return items


def extract_broker_fee(text: str, source_file: str) -> ExtractedField:
    fee = extract_amount_near_label(
        text, ["중개보수", "중개수수료"], source_file, "중개보수"
    )
    vat = extract_amount_near_label(
        text, ["부가세", "부가가치세"], source_file, "중개보수 부가세"
    )
    if fee.value is not None and vat.value is not None:
        fee.note = f"부가세 별도 확인됨: {vat.value:,}원 (매입세액공제 여부는 과세유형별 검토 필요)"
    elif fee.value is not None:
        fee.note = "부가세 표기를 찾지 못함 — 포함/별도 여부 원문 확인 필요"
    return fee


def extract_property_type(text: str, source_file: str) -> ExtractedField:
    for ptype, keywords in _PROPERTY_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return ExtractedField(
                    label="물건종류", value=ptype, confidence="검토필요",
                    evidence=Evidence(source_file=source_file, snippet=kw),
                    note="키워드 기반 추정 — 실제 물건 종류 확인 필요",
                )
    return ExtractedField(
        label="물건종류", value=None, confidence="미확인/누락",
        note="물건 종류를 추정할 키워드를 찾지 못함",
    )
