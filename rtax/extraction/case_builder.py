"""여러 DocumentRecord를 물건 하나(CaseData)로 묶습니다.

매매계약서/중개사영수증처럼 '매수용'과 '매도용'이 같은 양식인 증빙은
문서 자체만으로는 역할(매수/매도)을 알 수 없는 경우가 많습니다.
이 모듈은 계약일 순서(이른 날짜=매수, 늦은 날짜=매도)로 1차 판단하고,
그 판단은 항상 review_notes에 '확인 필요'로 남깁니다 — 숫자를 임의로 추정하지 않되,
역할 배정 로직은 투명하게 기록합니다.
"""
from typing import List, Optional

from rtax.models import CaseData, DocumentRecord, DocType, ExtractedField, REQUIRED_SLOTS


def _sort_key(d: DocumentRecord) -> str:
    return d.contract_date or "9999-99-99"


def _missing(label: str, note: str) -> ExtractedField:
    return ExtractedField(label=label, value=None, confidence="미확인/누락", note=note)


def build_case(documents: List[DocumentRecord], case_id: str) -> CaseData:
    case = CaseData(case_id=case_id, documents=documents)

    contracts = sorted(
        [d for d in documents if d.doc_type in (DocType.SALES_CONTRACT, DocType.AUCTION_PAYMENT_CERT)],
        key=_sort_key,
    )
    notary_docs = [d for d in documents if d.doc_type == DocType.NOTARY_RECEIPT]
    brokers = sorted([d for d in documents if d.doc_type == DocType.BROKER_RECEIPT], key=_sort_key)

    purchase_doc: Optional[DocumentRecord] = contracts[0] if len(contracts) >= 1 else None
    sale_doc: Optional[DocumentRecord] = contracts[-1] if len(contracts) >= 2 else None

    if len(contracts) >= 2:
        case.review_notes.append(
            "매수/매도계약서 역할은 계약일 순서로 자동판단함(이른 날짜=매수계약서, 늦은 날짜=매도계약서) "
            "— 세무대리인이 실제 매수인/매도인 당사자를 확인 필요"
        )
    elif len(contracts) == 1:
        case.review_notes.append("매매계약서(류)가 1건만 확인됨 — 매수/매도 중 어느 쪽인지 확인 필요")

    if purchase_doc is None:
        case.missing_docs.append(REQUIRED_SLOTS[0])
    if sale_doc is None:
        case.missing_docs.append(REQUIRED_SLOTS[3])
    if not notary_docs:
        case.missing_docs.append(REQUIRED_SLOTS[1])
    if len(brokers) == 0:
        case.missing_docs.append(REQUIRED_SLOTS[2])
        case.missing_docs.append(REQUIRED_SLOTS[4])
    elif len(brokers) == 1:
        case.review_notes.append(
            "중개사영수증이 1건만 확인됨 — 매수/매도 중 어느 쪽 건인지, 나머지 1건 누락 여부 확인 필요"
        )

    if purchase_doc:
        case.address = purchase_doc.fields.get("소재지")
        case.property_type = purchase_doc.fields.get("물건종류")
        case.area = purchase_doc.fields.get("면적")
        case.purchase_contract_date = purchase_doc.fields.get("계약일")
        case.acquisition_date = purchase_doc.fields.get("잔금청산일")
        case.acquisition_price = purchase_doc.fields.get("매매대금")

    if sale_doc:
        case.address = case.address or sale_doc.fields.get("소재지")
        case.property_type = case.property_type or sale_doc.fields.get("물건종류")
        case.area = case.area or sale_doc.fields.get("면적")
        case.sale_contract_date = sale_doc.fields.get("계약일")
        case.transfer_date = sale_doc.fields.get("잔금청산일")
        case.transfer_price = sale_doc.fields.get("매매대금")

    for nd in notary_docs:
        for key, f in nd.fields.items():
            if key == "영수증일자":
                continue
            case.notary_items.append(f)

    if len(brokers) >= 2:
        case.broker_fee_buy = brokers[0].fields.get("중개보수")
        case.broker_fee_sell = brokers[-1].fields.get("중개보수")
        case.review_notes.append("중개사영수증 매수/매도 역할은 영수증일자 순서로 자동판단함 — 확인 필요")
    elif len(brokers) == 1:
        case.broker_fee_buy = brokers[0].fields.get("중개보수")

    # 비어있는 필수 필드는 전부 '미확인/누락' 플레이스홀더로 채워서,
    # 이후 리포트/엑셀 단계가 None을 따로 처리하지 않아도 되게 한다.
    case.address = case.address or _missing("소재지", "계약서 증빙이 없어 주소를 확인할 수 없음")
    case.property_type = case.property_type or _missing("물건종류", "계약서 증빙이 없어 물건종류를 확인할 수 없음")
    case.area = case.area or _missing("면적", "계약서 증빙이 없어 면적을 확인할 수 없음")
    case.purchase_contract_date = case.purchase_contract_date or _missing("매수계약일", "매수계약서 없음")
    case.acquisition_date = case.acquisition_date or _missing("잔금청산일(취득일)", "매수계약서 없음")
    case.sale_contract_date = case.sale_contract_date or _missing("매도계약일", "매도계약서 없음")
    case.transfer_date = case.transfer_date or _missing("양도일", "매도계약서 없음")
    case.transfer_price = case.transfer_price or _missing("양도가액", "매도계약서 없음")
    case.acquisition_price = case.acquisition_price or _missing("취득가액", "매수계약서 없음")
    case.broker_fee_buy = case.broker_fee_buy or _missing("매수시 중개보수", "매수시 중개사영수증 없음")
    case.broker_fee_sell = case.broker_fee_sell or _missing("매도시 중개보수", "매도시 중개사영수증 없음")
    if not case.notary_items:
        case.notary_items = [_missing("법무사영수증 항목", "법무사영수증 없음")]

    review_candidates = [
        case.address, case.property_type, case.area,
        case.purchase_contract_date, case.acquisition_date,
        case.sale_contract_date, case.transfer_date,
        case.transfer_price, case.acquisition_price,
        case.broker_fee_buy, case.broker_fee_sell,
    ] + case.notary_items
    for f in review_candidates:
        if f.confidence == "미확인/누락":
            case.review_notes.append(f"[{f.label}] 미확인/누락 — {f.note}")

    return case
