from rtax.extraction.case_builder import build_case
from rtax.matching.reconciler import reconcile
from rtax.models import DocType, DocumentRecord, ExtractedField, LedgerEntry


def _doc(doc_type, contract_date, fields):
    return DocumentRecord(file_path="x.pdf", doc_type=doc_type, raw_text="", contract_date=contract_date, fields=fields)


def _build_simple_case():
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {
        "매매대금": ExtractedField("매매대금", 500_000_000),
        "잔금청산일": ExtractedField("잔금청산일", "2026-02-28"),
    })
    sale = _doc(DocType.SALES_CONTRACT, "2026-09-10", {
        "매매대금": ExtractedField("매매대금", 700_000_000),
        "잔금청산일": ExtractedField("잔금청산일", "2026-11-15"),
    })
    return build_case([purchase, sale], case_id="케이스")


def test_exact_match_marks_ilchi():
    case = _build_simple_case()
    ledger = [LedgerEntry(date="2026-02-28", description="매수대금 지급", counterparty="x",
                           supply_amount=None, vat_amount=None, total_amount=500_000_000)]
    results = reconcile(case, ledger, counterparty_name="[매매물건] x")
    buy = next(r for r in results if r.label == "매수대금(취득가액)")
    assert buy.status == "일치"


def test_amount_mismatch_marks_bulilchi():
    case = _build_simple_case()
    ledger = [LedgerEntry(date="2026-02-28", description="매수대금 지급", counterparty="x",
                           supply_amount=None, vat_amount=None, total_amount=499_000_000)]
    results = reconcile(case, ledger, counterparty_name="[매매물건] x")
    buy = next(r for r in results if r.label == "매수대금(취득가액)")
    assert buy.status == "불일치"


def test_no_ledger_entry_marks_missing_from_voucher():
    case = _build_simple_case()
    results = reconcile(case, [], counterparty_name="[매매물건] x")
    buy = next(r for r in results if r.label == "매수대금(취득가액)")
    assert buy.status == "누락(전표 미입력)"


def test_missing_evidence_marks_missing_from_docs():
    case = _build_simple_case()
    # 중개보수 증빙 자체가 없는 상태 (case_builder가 자동으로 미확인/누락 처리)
    results = reconcile(case, [], counterparty_name="[매매물건] x")
    fee = next(r for r in results if r.label == "매수시 중개보수")
    assert fee.status == "누락(증빙 미확보)"


def test_exact_match_elsewhere_is_not_stolen_by_unrelated_expected_entry():
    """회귀 테스트: 매수시 중개보수(2,000,000)에 가까운 날짜의 무관한 전표
    (법무사 수수료 15,000,000)가 먼저 처리된다는 이유로 억지로 '불일치'
    매칭되면 안 된다. 정확히 일치하는 짝(법무사영수증-취득세 15,000,000)이
    따로 있다면 그쪽이 우선 배정되어야 한다."""
    purchase = _doc(DocType.SALES_CONTRACT, "2026-01-15", {
        "매매대금": ExtractedField("매매대금", 500_000_000),
        "잔금청산일": ExtractedField("잔금청산일", "2026-02-28"),
    })
    sale = _doc(DocType.SALES_CONTRACT, "2026-09-10", {
        "매매대금": ExtractedField("매매대금", 700_000_000),
        "잔금청산일": ExtractedField("잔금청산일", "2026-11-15"),
    })
    notary = _doc(DocType.NOTARY_RECEIPT, "2026-02-28", {
        "취득세": ExtractedField("취득세", 15_000_000),
    })
    broker_buy = _doc(DocType.BROKER_RECEIPT, "2026-02-28", {
        "중개보수": ExtractedField("중개보수", 2_000_000),
    })
    case = build_case([purchase, sale, notary, broker_buy], case_id="회귀테스트")

    ledger = [
        LedgerEntry(date="2026-01-15", description="매수대금 지급", counterparty="x",
                    supply_amount=None, vat_amount=None, total_amount=500_000_000),
        LedgerEntry(date="2026-02-28", description="법무사 수수료", counterparty="x",
                    supply_amount=None, vat_amount=None, total_amount=15_000_000),
        LedgerEntry(date="2026-09-10", description="매도대금 수취", counterparty="x",
                    supply_amount=None, vat_amount=None, total_amount=700_000_000),
    ]
    results = reconcile(case, ledger, counterparty_name="[매매물건] x")

    notary_item = next(r for r in results if r.label == "법무사영수증-취득세")
    buy_fee = next(r for r in results if r.label == "매수시 중개보수")

    assert notary_item.status == "일치"
    assert notary_item.ledger_amount == 15_000_000
    assert buy_fee.status == "누락(전표 미입력)"
