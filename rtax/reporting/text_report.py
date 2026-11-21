"""5개 섹션 구조의 요약 리포트(문자열)를 생성합니다."""
from typing import List

from rtax.journal.journal_builder import counterparty_name
from rtax.models import REQUIRED_SLOTS, CaseData, JournalLine, MatchResult


def _fmt_amount(v) -> str:
    if v is None:
        return "[미확인/누락]"
    return f"{v:,.0f}원"


def _fmt_field(f) -> str:
    if f is None or f.value is None:
        return "[미확인/누락]"
    if isinstance(f.value, (int, float)):
        return _fmt_amount(f.value)
    return str(f.value)


def render(case: CaseData, match_results: List[MatchResult], journal_lines: List[JournalLine]) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append(f"물건: {case.case_id}")
    lines.append("=" * 60)

    lines.append("\n[1] 증빙 접수 및 누락 체크리스트")
    if case.missing_docs:
        for slot in REQUIRED_SLOTS:
            status = "미확인/누락" if slot in case.missing_docs else "접수 확인됨"
            lines.append(f"  - {slot}: {status}")
    else:
        lines.append("  - 5대 기본 증빙 모두 접수 확인됨")

    lines.append("\n[2] 부동산 기본정보 및 매매차익 예정신고 기초 내역")
    lines.append(f"  소재지: {_fmt_field(case.address)}")
    lines.append(f"  물건종류: {_fmt_field(case.property_type)}"
                  + ("  (키워드 기반 추정 — 확인 필요)" if case.property_type and case.property_type.confidence == "검토필요" else ""))
    lines.append(f"  면적: {_fmt_field(case.area)}")
    lines.append(f"  매수계약일: {_fmt_field(case.purchase_contract_date)}")
    lines.append(f"  잔금청산일(취득일): {_fmt_field(case.acquisition_date)}")
    lines.append(f"  매도계약일: {_fmt_field(case.sale_contract_date)}")
    lines.append(f"  양도일: {_fmt_field(case.transfer_date)}")
    lines.append(f"  양도가액: {_fmt_field(case.transfer_price)}")
    lines.append(f"  취득가액: {_fmt_field(case.acquisition_price)}")
    lines.append("  법무사영수증 항목:")
    for item in case.notary_items:
        lines.append(f"    - {item.label}: {_fmt_field(item)}")
    lines.append(f"  매수시 중개보수: {_fmt_field(case.broker_fee_buy)}")
    lines.append(f"  매도시 중개보수: {_fmt_field(case.broker_fee_sell)}")
    lines.append("  ※ 매매차익 기초금액 = 양도가액 - (취득가액 + 취득부대비용 + 양도비) "
                 "— 세부 가감·공제·세율 적용은 세무대리인 최종 검토 대상")

    lines.append("\n[3] 위하고(WEHAGO) 자동전표 대조 결과")
    for m in match_results:
        lines.append(
            f"  - {m.label}: 증빙 {_fmt_amount(m.evidence_amount)} / 전표 {_fmt_amount(m.ledger_amount)} "
            f"/ 상태: {m.status}" + (f" ({m.note})" if m.note else "")
        )

    lines.append("\n[4] 부동산 주소지 거래처 기준 위하고 전표 입력 초안")
    lines.append(f"  거래처명(안): {counterparty_name(case)}")
    for j in journal_lines:
        lines.append(
            f"  - 차변[{j.debit_account}] / 대변[{j.credit_account}] / {_fmt_amount(j.amount)} "
            f"/ 적요: {j.description} / 상태: {j.status}"
            + (f" / 확인필요: {j.review_note}" if j.review_note else "")
        )

    lines.append("\n[5] 세무대리인 최종 확인 사항")
    if case.review_notes:
        for note in case.review_notes:
            lines.append(f"  - {note}")
    else:
        lines.append("  - 특별히 판단이 필요한 항목 없음 (단, 전체 수치는 최종 검토 필수)")

    return "\n".join(lines)
