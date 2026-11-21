from rtax.extraction import field_rules


SAMPLE_CONTRACT = """
부동산매매계약서
소재지: 서울특별시 강남구 역삼동 123-45
전용면적 84.95㎡
매매대금 일금 칠억원정(₩700,000,000)
계약일 2026년 09월 10일
잔금지급일 2026.11.15
"""


def test_extract_address():
    f = field_rules.extract_address(SAMPLE_CONTRACT, "contract.pdf")
    assert "서울특별시 강남구 역삼동" in f.value
    assert f.confidence == "확인"


def test_extract_area():
    f = field_rules.extract_area(SAMPLE_CONTRACT, "contract.pdf")
    assert "84.95" in f.value
    assert "㎡" in f.value


def test_extract_date_near_label_contract_date():
    f = field_rules.extract_date_near_label(SAMPLE_CONTRACT, ["계약일"], "contract.pdf", "계약일")
    assert f.value == "2026-09-10"


def test_extract_date_near_label_settlement():
    f = field_rules.extract_date_near_label(
        SAMPLE_CONTRACT, ["잔금지급일", "잔금일"], "contract.pdf", "잔금청산일"
    )
    assert f.value == "2026-11-15"


def test_extract_amount_near_label_total_price():
    f = field_rules.extract_amount_near_label(
        SAMPLE_CONTRACT, ["매매대금"], "contract.pdf", "매매대금"
    )
    assert f.value == 700_000_000


def test_missing_field_is_flagged():
    f = field_rules.extract_date_near_label("아무 내용 없음", ["계약일"], "x.pdf", "계약일")
    assert f.value is None
    assert f.confidence == "미확인/누락"


NOTARY_SAMPLE = """
법무사 수수료 영수증
취득세 15,000,000원
지방교육세 1,500,000원
등기신청수수료 150,000원
법무사보수 500,000원
"""


def test_extract_notary_items():
    items = field_rules.extract_notary_items(NOTARY_SAMPLE, "notary.pdf")
    labels = {i.label: i.value for i in items}
    assert labels["취득세"] == 15_000_000
    assert labels["법무사보수"] == 500_000
