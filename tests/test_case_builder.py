from rtax.extraction.case_builder import build_case
from rtax.models import DocType, DocumentRecord, ExtractedField


def _doc(doc_type, contract_date, fields):
    return DocumentRecord(
        file_path=f"{doc_type}_{contract_date}.pdf",
        doc_type=doc_type,
        raw_text="",
        contract_date=contract_date,
        fields=fields,
    )


def test_two_contracts_assign_purchase_and_sale_by_date():
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {
        "소재지": ExtractedField("소재지", "서울시 강남구 역삼동 123-45"),
        "매매대금": ExtractedField("매매대금", 500_000_000),
        "계약일": ExtractedField("계약일", "2026-01-15"),
        "잔금청산일": ExtractedField("잔금청산일", "2026-02-28"),
    })
    sale = _doc(DocType.SALES_CONTRACT, "2026-09-10", {
        "매매대금": ExtractedField("매매대금", 700_000_000),
        "계약일": ExtractedField("계약일", "2026-09-10"),
        "잔금청산일": ExtractedField("잔금청산일", "2026-11-15"),
    })
    case = build_case([purchase, sale], case_id="테스트물건")

    assert case.acquisition_price.value == 500_000_000
    assert case.transfer_price.value == 700_000_000
    assert case.purchase_contract_date.value == "2026-01-15"
    assert case.sale_contract_date.value == "2026-09-10"
    assert any("자동판단" in n for n in case.review_notes)
    assert "매도계약서" not in case.missing_docs
    assert "매수계약서(또는 경락대금완납증명원)" not in case.missing_docs


def test_missing_broker_receipts_flagged():
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {"매매대금": ExtractedField("매매대금", 1)})
    sale = _doc(DocType.SALES_CONTRACT, "2026-09-10", {"매매대금": ExtractedField("매매대금", 2)})
    notary = _doc(DocType.NOTARY_RECEIPT, "2026-02-28", {"취득세": ExtractedField("취득세", 100)})

    case = build_case([purchase, sale, notary], case_id="테스트물건2")

    assert "매수시 중개사영수증" in case.missing_docs
    assert "매도시 중개사영수증" in case.missing_docs
    assert case.broker_fee_buy.confidence == "미확인/누락"


def test_no_documents_everything_missing():
    case = build_case([], case_id="빈물건")
    assert len(case.missing_docs) == 5
    assert case.address.value is None
