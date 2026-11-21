"""부동산 주소지 기준 거래처명으로 위하고 분개 초안을 만듭니다."""
from typing import List

from rtax.journal.account_rules import rule_for_label
from rtax.models import CaseData, JournalLine, MatchResult

_STATUS_MAP = {
    "일치": "일치",
    "불일치": "수정필요",
    "누락(전표 미입력)": "신규입력",
    "누락(증빙 미확보)": "신규입력",
}


def counterparty_name(case: CaseData) -> str:
    addr = case.address.value if case.address and case.address.value else "[주소 미확인 — 직접 입력]"
    return f"[매매물건] {addr}"


def build_journal(case: CaseData, match_results: List[MatchResult]) -> List[JournalLine]:
    cp = counterparty_name(case)
    lines: List[JournalLine] = []

    known_amounts = []
    for m in match_results:
        rule = rule_for_label(m.label)
        amount = m.evidence_amount if m.evidence_amount is not None else m.ledger_amount
        if amount is not None:
            known_amounts.append((m.label, amount))

        note = rule["note"]
        if m.note:
            note = f"{note} / {m.note}" if note else m.note

        lines.append(JournalLine(
            debit_account=rule["debit"],
            credit_account=rule["credit"],
            counterparty=cp,
            amount=amount,
            description=m.label,
            status=_STATUS_MAP.get(m.status, "신규입력"),
            review_note=note.strip(" /"),
        ))

    cogs_note = "02시트 매매차익 산출과 연결 — 취득가액+취득부대비용 합계로 매출원가 대체"
    acquisition_related = {"매수대금(취득가액)"} | {
        l for l, _ in known_amounts if l.startswith("법무사영수증-")
    }
    cogs_amount = None
    if all(any(l == target for l, _ in known_amounts) for target in acquisition_related):
        cogs_amount = sum(a for l, a in known_amounts if l in acquisition_related)

    lines.append(JournalLine(
        debit_account="상품매출원가",
        credit_account="상품(부동산)",
        counterparty=cp,
        amount=cogs_amount,
        description="매출원가 대체",
        status="신규입력",
        review_note=cogs_note,
    ))

    return lines
