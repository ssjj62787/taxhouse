"""위하고(WEHAGO) 자동전표 내역(xlsx/csv)을 읽어 LedgerEntry 리스트로 변환.

위하고 다운로드 양식마다 컬럼명이 조금씩 달라서, 흔히 쓰이는 이름들을
별칭(alias)으로 매칭합니다. 매칭되는 컬럼이 없으면 해당 필드는 None으로 둡니다.
"""
from typing import List, Optional

from rtax.models import LedgerEntry

_ALIASES = {
    "date": ["일자", "날짜", "거래일자", "전표일자"],
    "description": ["적요", "내용", "설명"],
    "counterparty": ["거래처", "거래처명", "상대계정"],
    "supply_amount": ["공급가액", "공급가"],
    "vat_amount": ["부가세", "세액"],
    "total_amount": ["합계", "합계금액", "거래금액", "금액"],
}


def _find_col(columns, candidates) -> Optional[str]:
    for cand in candidates:
        for col in columns:
            if cand in col:
                return col
    return None


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if s == "" or s.lower() == "nan":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _clean_date(value) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    try:
        import pandas as pd
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return s


def load_ledger(path: str) -> List[LedgerEntry]:
    import pandas as pd

    if path.lower().endswith(".csv"):
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    else:
        df = pd.read_excel(path, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]

    col_date = _find_col(df.columns, _ALIASES["date"])
    col_desc = _find_col(df.columns, _ALIASES["description"])
    col_cp = _find_col(df.columns, _ALIASES["counterparty"])
    col_supply = _find_col(df.columns, _ALIASES["supply_amount"])
    col_vat = _find_col(df.columns, _ALIASES["vat_amount"])
    col_total = _find_col(df.columns, _ALIASES["total_amount"])

    entries: List[LedgerEntry] = []
    for _, row in df.iterrows():
        entries.append(LedgerEntry(
            date=_clean_date(row.get(col_date)) if col_date else None,
            description=(str(row.get(col_desc)).strip() if col_desc and row.get(col_desc) is not None else ""),
            counterparty=(str(row.get(col_cp)).strip() if col_cp and row.get(col_cp) is not None else None),
            supply_amount=_to_float(row.get(col_supply)) if col_supply else None,
            vat_amount=_to_float(row.get(col_vat)) if col_vat else None,
            total_amount=_to_float(row.get(col_total)) if col_total else None,
            raw=row.to_dict(),
        ))
    return entries
