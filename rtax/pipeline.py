"""전체 흐름을 한 번에 실행: 증빙 폴더 읽기 -> 분류/추출 -> 위하고 대조 -> 분개초안 -> 리포트."""
import os
from typing import Callable, Optional

from rtax.extraction.case_builder import build_case
from rtax.ingest.case_folder import load_case_documents
from rtax.journal.journal_builder import build_journal, counterparty_name
from rtax.matching.reconciler import reconcile
from rtax.reporting import excel_writer, text_report
from rtax.wehago.ledger_loader import load_ledger


def run_case(
    case_dir: str,
    wehago_path: Optional[str],
    out_xlsx_path: str,
    case_id: Optional[str] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> str:
    """증빙 폴더 + (선택) 위하고 전표 파일을 처리해서 xlsx 리포트를 저장하고,
    화면에 보여줄 5단 텍스트 리포트를 반환합니다.
    """
    def log(msg: str):
        if progress_cb:
            progress_cb(msg)

    case_id = case_id or os.path.basename(os.path.normpath(case_dir))

    log("증빙 폴더 읽는 중...")
    documents = load_case_documents(case_dir, progress_cb=progress_cb)

    log("증빙 분류 및 항목 추출 중...")
    case = build_case(documents, case_id=case_id)

    ledger = []
    if wehago_path:
        log("위하고 전표 불러오는 중...")
        ledger = load_ledger(wehago_path)
    else:
        case.review_notes.append("위하고 전표 파일이 지정되지 않아 대조를 수행하지 못함")

    log("전표 대조 중...")
    cp = counterparty_name(case)
    match_results = reconcile(case, ledger, counterparty_name=cp)

    log("분개초안 생성 중...")
    journal_lines = build_journal(case, match_results)

    log("엑셀 리포트 저장 중...")
    excel_writer.write_report(case, match_results, journal_lines, out_xlsx_path)

    log(f"완료: {out_xlsx_path}")
    return text_report.render(case, match_results, journal_lines)
