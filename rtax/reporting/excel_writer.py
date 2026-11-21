"""실제 추출/대조/분개 결과를 5개 시트의 xlsx 파일로 저장합니다."""
from typing import List

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from rtax.journal.journal_builder import counterparty_name
from rtax.models import REQUIRED_SLOTS, CaseData, JournalLine, MatchResult

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(bold=True, size=13, color="1F4E78")
NOTE_FONT = Font(italic=True, size=9, color="808080")
WARN_FILL = PatternFill("solid", fgColor="FFF2CC")
REVIEW_FILL = PatternFill("solid", fgColor="FCE4D6")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_C = Alignment(wrap_text=True, vertical="center", horizontal="center")


def _style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = WRAP_C
        cell.border = BORDER


def _style_row(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.alignment = WRAP
        cell.border = BORDER


def _set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _field_value(f):
    return f.value if f is not None else None


def _write_checklist_sheet(wb, case: CaseData):
    ws = wb.create_sheet("01_증빙체크리스트")
    ws["A1"] = "증빙 접수 및 누락 체크리스트"
    ws["A1"].font = TITLE_FONT
    headers = ["증빙명", "접수상태"]
    hr = 3
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    _style_header(ws, hr, len(headers))

    r = hr + 1
    for slot in REQUIRED_SLOTS:
        status = "미확인/누락" if slot in case.missing_docs else "접수 확인됨"
        ws.cell(row=r, column=1, value=slot)
        ws.cell(row=r, column=2, value=status)
        _style_row(ws, r, len(headers))
        if status == "미확인/누락":
            ws.cell(row=r, column=2).fill = WARN_FILL
        r += 1
    _set_widths(ws, [46, 18])


def _write_basic_info_sheet(wb, case: CaseData):
    ws = wb.create_sheet("02_기초내역_매매차익")
    ws["A1"] = "부동산 기본정보 및 매매차익 예정신고 기초 내역"
    ws["A1"].font = TITLE_FONT

    ws["A3"] = "① 물건 개요"
    ws["A3"].font = Font(bold=True, size=11)
    hr = 4
    for c, h in enumerate(["항목", "내용", "비고"], start=1):
        ws.cell(row=hr, column=c, value=h)
    _style_header(ws, hr, 3)

    info_rows = [
        ("소재지", case.address),
        ("물건종류", case.property_type),
        ("면적", case.area),
        ("매수계약일", case.purchase_contract_date),
        ("잔금청산일(취득일)", case.acquisition_date),
        ("매도계약일", case.sale_contract_date),
        ("양도일", case.transfer_date),
    ]
    r = hr + 1
    for label, f in info_rows:
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=_field_value(f))
        ws.cell(row=r, column=3, value=(f.note if f else ""))
        _style_row(ws, r, 3)
        if f is None or f.value is None:
            ws.cell(row=r, column=2).fill = WARN_FILL
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="② 매매차익 산출").font = Font(bold=True, size=11)
    r += 1
    hr2 = r
    for c, h in enumerate(["구분", "세부 항목", "가감", "금액(원)", "비고"], start=1):
        ws.cell(row=hr2, column=c, value=h)
    _style_header(ws, hr2, 5)

    calc_rows = [
        ("양도가액", "매도계약서상 매매대금", "+", case.transfer_price),
        ("취득가액", "매수대금(경락대금 포함 가능)", "-", case.acquisition_price),
    ]
    for item in case.notary_items:
        calc_rows.append(("취득부대비용", f"법무사영수증: {item.label}", "-", item))
    calc_rows.append(("양도비 등", "매수시 중개보수", "-", case.broker_fee_buy))
    calc_rows.append(("양도비 등", "매도시 중개보수", "-", case.broker_fee_sell))

    r = hr2 + 1
    first_data_row = r
    for gubun, detail, sign, f in calc_rows:
        ws.cell(row=r, column=1, value=gubun)
        ws.cell(row=r, column=2, value=detail)
        ws.cell(row=r, column=3, value=sign)
        ws.cell(row=r, column=4, value=_field_value(f))
        ws.cell(row=r, column=5, value=(f.note if f else ""))
        ws.cell(row=r, column=4).number_format = "#,##0"
        _style_row(ws, r, 5)
        if f is None or f.value is None:
            ws.cell(row=r, column=4).fill = WARN_FILL
        r += 1
    last_data_row = r - 1

    dv_sign = DataValidation(type="list", formula1='"+,-"', allow_blank=False)
    ws.add_data_validation(dv_sign)
    dv_sign.add(f"C{first_data_row}:C{last_data_row}")

    result_row = r + 1
    ws.cell(row=result_row, column=1, value="매매차익 예정신고 기초금액 (미확인/누락 항목이 있으면 참고용)").font = Font(bold=True)
    formula = (
        f'=SUMIF(C{first_data_row}:C{last_data_row},"+",D{first_data_row}:D{last_data_row})'
        f'-SUMIF(C{first_data_row}:C{last_data_row},"-",D{first_data_row}:D{last_data_row})'
    )
    ws.cell(row=result_row, column=4, value=formula)
    ws.cell(row=result_row, column=4).number_format = "#,##0"
    ws.cell(row=result_row, column=4).font = Font(bold=True, color="C00000")
    ws.cell(row=result_row + 1, column=1, value="※ 세법상 세부 가감·공제·세율 적용은 세무대리인 최종 검토 대상").font = NOTE_FONT

    _set_widths(ws, [18, 44, 6, 16, 42])


def _write_reconcile_sheet(wb, case: CaseData, match_results: List[MatchResult]):
    ws = wb.create_sheet("03_위하고대조")
    ws["A1"] = "위하고(WEHAGO) 자동전표 대조 결과"
    ws["A1"].font = TITLE_FONT
    headers = ["구분", "거래처(주소기준)", "일자", "증빙상 금액", "전표상 금액", "대조상태", "비고"]
    hr = 3
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    _style_header(ws, hr, len(headers))

    cp = counterparty_name(case)
    r = hr + 1
    for m in match_results:
        ws.cell(row=r, column=1, value=m.label)
        ws.cell(row=r, column=2, value=cp)
        ws.cell(row=r, column=3, value=m.date)
        ws.cell(row=r, column=4, value=m.evidence_amount)
        ws.cell(row=r, column=5, value=m.ledger_amount)
        ws.cell(row=r, column=6, value=m.status)
        ws.cell(row=r, column=7, value=m.note)
        for col in (4, 5):
            ws.cell(row=r, column=col).number_format = "#,##0"
        _style_row(ws, r, len(headers))
        if m.status != "일치":
            ws.cell(row=r, column=6).fill = WARN_FILL
        r += 1

    _set_widths(ws, [22, 32, 13, 16, 16, 18, 36])


def _write_journal_sheet(wb, case: CaseData, journal_lines: List[JournalLine]):
    ws = wb.create_sheet("04_분개초안")
    ws["A1"] = "부동산 주소지 거래처 기준 위하고 전표 입력 초안"
    ws["A1"].font = TITLE_FONT
    headers = ["차변계정(안)", "대변계정(안)", "거래처(주소기준)", "금액", "적요", "대조상태", "확인 필요사항"]
    hr = 3
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    _style_header(ws, hr, len(headers))

    r = hr + 1
    for j in journal_lines:
        ws.cell(row=r, column=1, value=j.debit_account)
        ws.cell(row=r, column=2, value=j.credit_account)
        ws.cell(row=r, column=3, value=j.counterparty)
        ws.cell(row=r, column=4, value=j.amount)
        ws.cell(row=r, column=5, value=j.description)
        ws.cell(row=r, column=6, value=j.status)
        ws.cell(row=r, column=7, value=j.review_note)
        ws.cell(row=r, column=4).number_format = "#,##0"
        _style_row(ws, r, len(headers))
        if j.review_note:
            ws.cell(row=r, column=7).fill = REVIEW_FILL
        r += 1

    _set_widths(ws, [24, 16, 32, 16, 26, 12, 40])


def _write_final_review_sheet(wb, case: CaseData):
    ws = wb.create_sheet("05_최종확인사항")
    ws["A1"] = "세무대리인 최종 확인 사항"
    ws["A1"].font = TITLE_FONT
    headers = ["확인 필요 내용", "확인 여부"]
    hr = 3
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    _style_header(ws, hr, len(headers))

    r = hr + 1
    notes = case.review_notes or ["특별히 판단이 필요한 항목 없음 (단, 전체 수치는 최종 검토 필수)"]
    for note in notes:
        ws.cell(row=r, column=1, value=note)
        ws.cell(row=r, column=2, value="미확인")
        _style_row(ws, r, len(headers))
        r += 1

    dv = DataValidation(type="list", formula1='"확인완료,미확인"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"B{hr+1}:B{r-1}")
    _set_widths(ws, [70, 14])


def write_report(case: CaseData, match_results: List[MatchResult], journal_lines: List[JournalLine], out_path: str):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    _write_checklist_sheet(wb, case)
    _write_basic_info_sheet(wb, case)
    _write_reconcile_sheet(wb, case, match_results)
    _write_journal_sheet(wb, case, journal_lines)
    _write_final_review_sheet(wb, case)
    wb.save(out_path)
