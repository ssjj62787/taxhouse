"""대조 결과 라벨 -> 계정과목(안) 매핑 규칙.

계정 분류가 애매한 항목(취득세 등 자본적지출 여부, 중개보수 부가세 공제 여부)은
반드시 note에 '세무사 확인' 문구를 남겨서 분개초안 시트에서 눈에 띄게 합니다.
"""

SIMPLE_RULES = {
    "매수대금(취득가액)": {"debit": "상품(부동산)", "credit": "보통예금", "note": ""},
    "매도대금(양도가액)": {"debit": "보통예금", "credit": "상품매출", "note": ""},
    "매수시 중개보수": {
        "debit": "수수료비용 또는 상품(부동산)", "credit": "보통예금",
        "note": "부가세 매입세액공제 여부(사업자 과세유형) 세무사 확인 필요",
    },
    "매도시 중개보수": {"debit": "수수료비용", "credit": "보통예금", "note": ""},
}

NOTARY_FEE_LABELS = {"법무사보수"}

DEFAULT_RULE = {"debit": "미분류", "credit": "미분류", "note": "계정 매핑 규칙 없음 — 직접 지정 필요"}


def rule_for_label(label: str) -> dict:
    if label in SIMPLE_RULES:
        return SIMPLE_RULES[label]
    if label.startswith("법무사영수증-"):
        item = label.split("-", 1)[1]
        if item in NOTARY_FEE_LABELS:
            return {
                "debit": "수수료비용 또는 상품(부동산)", "credit": "보통예금",
                "note": "부가세 매입세액공제 여부(사업자 과세유형) 세무사 확인 필요",
            }
        return {
            "debit": "상품(부동산) 또는 세금과공과", "credit": "보통예금",
            "note": "재고자산 취득원가 가산 대상인지 단순비용인지 세무사 확인 필요",
        }
    return DEFAULT_RULE
