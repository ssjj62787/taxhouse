"""증빙에서 뽑은 기대값과 위하고 전표를 대조해 일치/불일치/누락을 판정합니다.

2단계로 매칭합니다:
  1단계: 금액이 정확히 일치(허용오차 이내)하는 쌍을 먼저 전역적으로 확정합니다.
         (expected 항목 처리 순서에 따라 "먼저 온 항목이 엉뚱한 전표를 선점"하는
         문제를 막기 위해, 모든 expected x ledger 조합 중 diff가 작은 것부터 배정합니다.)
  2단계: 1단계에서 못 찾은 항목만, 날짜가 가까운(허용오차 이내) 남은 전표를
         '같은 거래인데 금액이 다름(불일치)'으로 봅니다. 날짜도 가까운 후보가
         없으면 억지로 엮지 않고 '누락(전표 미입력)'으로 둡니다.
"""
from datetime import datetime
from typing import List, Optional

from rtax import config
from rtax.models import CaseData, LedgerEntry, MatchResult


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def _date_diff_days(a: Optional[str], b: Optional[str]) -> Optional[int]:
    da, db = _parse_date(a), _parse_date(b)
    if da is None or db is None:
        return None
    return abs((da - db).days)


def _ledger_amount(entry: LedgerEntry) -> Optional[float]:
    if entry.total_amount is not None:
        return entry.total_amount
    if entry.supply_amount is not None:
        return entry.supply_amount + (entry.vat_amount or 0)
    return None


def _build_expected_entries(case: CaseData):
    """(라벨, 기대금액 ExtractedField, 기준일자 문자열) 리스트."""
    entries = [
        ("매수대금(취득가액)", case.acquisition_price, case.acquisition_date.value),
        ("매수시 중개보수", case.broker_fee_buy, case.acquisition_date.value),
        ("매도대금(양도가액)", case.transfer_price, case.transfer_date.value),
        ("매도시 중개보수", case.broker_fee_sell, case.transfer_date.value),
    ]
    for item in case.notary_items:
        entries.append((f"법무사영수증-{item.label}", item, case.acquisition_date.value))
    return entries


def reconcile(case: CaseData, ledger: List[LedgerEntry], counterparty_name: str) -> List[MatchResult]:
    expected = _build_expected_entries(case)
    results: List[Optional[MatchResult]] = [None] * len(expected)

    pending = []  # idx 목록 (증빙 금액 자체가 있는 것만)
    for idx, (label, field_, ref_date) in enumerate(expected):
        if field_ is None or field_.value is None:
            results[idx] = MatchResult(
                label=label, evidence_amount=None, ledger_amount=None, date=ref_date,
                counterparty=counterparty_name, status="누락(증빙 미확보)",
                note=field_.note if field_ else "증빙 자체가 없음",
            )
        else:
            pending.append(idx)

    used_ledger = set()

    # 1단계: 금액이 정확히 맞는 쌍을 diff가 작은 순서로 전역 배정
    exact_candidates = []  # (diff, date_gap, idx, ledger_idx)
    for idx in pending:
        label, field_, ref_date = expected[idx]
        expected_amount = float(field_.value)
        for li, entry in enumerate(ledger):
            amt = _ledger_amount(entry)
            if amt is None:
                continue
            diff = abs(amt - expected_amount)
            if diff <= config.AMOUNT_TOLERANCE_WON:
                date_gap = _date_diff_days(ref_date, entry.date)
                exact_candidates.append((diff, date_gap if date_gap is not None else 10**9, idx, li))
    exact_candidates.sort(key=lambda t: (t[0], t[1]))

    matched_idx = set()
    for diff, _gap, idx, li in exact_candidates:
        if idx in matched_idx or li in used_ledger:
            continue
        matched_idx.add(idx)
        used_ledger.add(li)
        label, field_, ref_date = expected[idx]
        entry = ledger[li]
        results[idx] = MatchResult(
            label=label, evidence_amount=float(field_.value), ledger_amount=_ledger_amount(entry),
            date=entry.date or ref_date, counterparty=counterparty_name, status="일치", note="",
        )

    # 2단계: 남은 항목은 날짜가 가까운 전표만 '불일치' 후보로 보고, 없으면 누락 처리
    for idx in pending:
        if idx in matched_idx:
            continue
        label, field_, ref_date = expected[idx]
        expected_amount = float(field_.value)

        best = None  # (diff, ledger_idx)
        for li, entry in enumerate(ledger):
            if li in used_ledger:
                continue
            date_gap = _date_diff_days(ref_date, entry.date)
            if date_gap is None or date_gap > config.DATE_TOLERANCE_DAYS:
                continue
            amt = _ledger_amount(entry)
            if amt is None:
                continue
            diff = abs(amt - expected_amount)
            if best is None or diff < best[0]:
                best = (diff, li)

        if best is None:
            results[idx] = MatchResult(
                label=label, evidence_amount=expected_amount, ledger_amount=None,
                date=ref_date, counterparty=counterparty_name,
                status="누락(전표 미입력)", note="증빙상 금액과 대응하는 위하고 전표를 찾지 못함",
            )
        else:
            diff, li = best
            used_ledger.add(li)
            entry = ledger[li]
            ledger_amt = _ledger_amount(entry)
            results[idx] = MatchResult(
                label=label, evidence_amount=expected_amount, ledger_amount=ledger_amt,
                date=entry.date or ref_date, counterparty=counterparty_name,
                status="불일치",
                note=f"증빙 {expected_amount:,.0f}원 vs 전표 {ledger_amt:,.0f}원 (차액 {diff:,.0f}원, 날짜는 근접)",
            )

    return results  # type: ignore[return-value]
