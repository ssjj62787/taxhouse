from rtax.extraction.case_builder import build_case
from rtax.journal.journal_builder import build_journal, counterparty_name
from rtax.matching.reconciler import reconcile
from rtax.models import DocType, DocumentRecord, ExtractedField


def _doc(doc_type, contract_date, fields):
    return DocumentRecord(file_path="x.pdf", doc_type=doc_type, raw_text="", contract_date=contract_date, fields=fields)


def test_counterparty_name_uses_address():
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {
        "소재지": ExtractedField("소재지", "서울시 강남구 역삼동 123-45"),
    })
    case = build_case([purchase], case_id="케이스")
    assert counterparty_name(case) == "[매매물건] 서울시 강남구 역삼동 123-45"


def test_journal_lines_flag_vat_review_for_broker_fee():
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {"매매대금": ExtractedField("매매대금", 500_000_000)})
    broker = _doc(DocType.BROKER_RECEIPT, "2026-02-28", {"중개보수": ExtractedField("중개보수", 2_000_000)})
    case = build_case([purchase, broker], case_id="케이스")
    results = reconcile(case, [], counterparty_name="[매매물건] x")
    lines = build_journal(case, results)

    buy_fee_line = next(l for l in lines if l.description == "매수시 중개보수")
    assert "세무사 확인" in buy_fee_line.review_note
    assert buy_fee_line.status == "신규입력"


def test_journal_includes_cogs_transfer_line():
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {"매매대금": ExtractedField("매매대금", 500_000_000)})
    case = build_case([purchase], case_id="케이스")
    results = reconcile(case, [], counterparty_name="[매매물건] x")
    lines = build_journal(case, results)
    assert any(l.description == "매출원가 대체" for l in lines)
