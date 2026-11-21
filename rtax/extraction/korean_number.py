"""한글 금액 표기(예: '금 삼억오천만원정')를 숫자로 변환.

우선순위: 아라비아 숫자가 괄호/원 기호와 함께 병기되어 있으면 그 값을 먼저 쓰고
(가장 신뢰도 높음), 없을 때만 한글 숫자를 직접 해석합니다.
"""
import re
from typing import Optional

_DIGIT = {
    "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
    "육": 6, "륙": 6, "칠": 7, "팔": 8, "구": 9,
}
_SMALL_UNIT = {"천": 1000, "백": 100, "십": 10}
_LARGE_UNIT = [("조", 10 ** 12), ("억", 10 ** 8), ("만", 10 ** 4)]

_ARABIC_NEAR_WON = re.compile(r"[₩]?\s*([0-9][0-9,]{2,})\s*(?:원|\))?")

# '원' 바로 앞에 붙은 한글숫자 구간만 후보로 본다 (문장 전체를 훑으면
# '문구', '구입' 같은 일반 단어의 숫자음(구=9 등)을 오탐하게 되므로).
_HANGUL_AMOUNT_NEAR_WON = re.compile(r"([일이삼사오육륙칠팔구십백천만억조]+)\s*원")
_UNIT_CHARS = set("십백천만억조")


def _parse_section(s: str) -> int:
    """조/억/만이 없는 한 구간(예: '이천오백')을 정수로 변환."""
    total = 0
    current = 0
    for ch in s:
        if ch in _DIGIT:
            current = _DIGIT[ch]
        elif ch in _SMALL_UNIT:
            total += (current if current else 1) * _SMALL_UNIT[ch]
            current = 0
        # 그 외 문자는 무시 (조사, 공백 등)
    total += current
    return total


def _parse_hangul_run(cleaned: str) -> Optional[int]:
    """'삼억오천만' 처럼 숫자음/단위로만 이루어진 한 구간을 정수로 변환."""
    # 억/만 단위 없이 '구', '칠' 한 글자만 있는 건 일반 단어의 숫자음(예: '문구')과
    # 구분할 수 없으므로, 최소한 하나의 단위 글자(십백천만억조)가 있어야만 금액으로 인정한다.
    if not any(ch in _UNIT_CHARS for ch in cleaned):
        return None

    value = 0
    remaining = cleaned
    for unit_char, unit_val in _LARGE_UNIT:
        if unit_char in remaining:
            idx = remaining.index(unit_char)
            section = remaining[:idx]
            section_val = _parse_section(section) if section else 1
            value += section_val * unit_val
            remaining = remaining[idx + 1:]
    value += _parse_section(remaining)
    return value if value > 0 else None


def _parse_hangul(text: str) -> Optional[int]:
    """텍스트 안에서 '~~원' 바로 앞의 한글숫자 구간을 찾아 변환.

    전체 텍스트를 무작정 숫자음으로 해석하면 '문구', '구입' 같은 일반 단어를
    숫자로 오인하므로, '원' 바로 앞에 붙어있는 구간만 후보로 삼는다.
    """
    for m in _HANGUL_AMOUNT_NEAR_WON.finditer(text):
        value = _parse_hangul_run(m.group(1))
        if value is not None:
            return value
    return None


def parse_korean_amount(text: str) -> Optional[int]:
    """'금 삼억오천만원정(₩350,000,000)' 같은 문자열에서 원화 금액(int)을 추출.

    아라비아 숫자 병기가 있으면 그 값 우선, 없으면 한글 숫자를 해석.
    인식 실패 시 None (호출부에서 [미확인/누락]으로 표시해야 함).
    """
    if not text:
        return None

    m = _ARABIC_NEAR_WON.search(text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass

    return _parse_hangul(text)
