"""원문 텍스트 한 건을 분류하고, 타입별 라벨 추출을 적용해 DocumentRecord로 만듭니다."""
from rtax.extraction import field_rules, document_classifier
from rtax.models import DocumentRecord, DocType

CONTRACT_DATE_LABELS = ["매매계약일", "계약일", "작성일"]
SETTLEMENT_DATE_LABELS = ["잔금지급일", "잔금일", "잔금", "등기접수일", "완납일", "납부일"]
TOTAL_PRICE_LABELS = ["총 매매대금", "총매매대금", "매매대금", "매매금액", "낙찰금액", "경락금액"]
NOTARY_DATE_LABELS = ["수납일", "발행일", "작성일"]
BROKER_DATE_LABELS = ["영수일", "발행일", "작성일", "수령일"]


def build_document_record(file_path: str, raw_text: str) -> DocumentRecord:
    doc_type = document_classifier.classify(raw_text)
    record = DocumentRecord(file_path=file_path, doc_type=doc_type, raw_text=raw_text)

    if doc_type in (DocType.SALES_CONTRACT, DocType.AUCTION_PAYMENT_CERT):
        record.fields["소재지"] = field_rules.extract_address(raw_text, file_path)
        record.fields["물건종류"] = field_rules.extract_property_type(raw_text, file_path)
        record.fields["면적"] = field_rules.extract_area(raw_text, file_path)
        contract_date_field = field_rules.extract_date_near_label(
            raw_text, CONTRACT_DATE_LABELS, file_path, "계약일")
        settlement_date_field = field_rules.extract_date_near_label(
            raw_text, SETTLEMENT_DATE_LABELS, file_path, "잔금청산일")
        price_field = field_rules.extract_amount_near_label(
            raw_text, TOTAL_PRICE_LABELS, file_path, "매매대금")
        record.fields["계약일"] = contract_date_field
        record.fields["잔금청산일"] = settlement_date_field
        record.fields["매매대금"] = price_field
        record.contract_date = contract_date_field.value or settlement_date_field.value

    elif doc_type == DocType.NOTARY_RECEIPT:
        for item in field_rules.extract_notary_items(raw_text, file_path):
            record.fields[item.label] = item
        date_field = field_rules.extract_date_near_label(
            raw_text, NOTARY_DATE_LABELS, file_path, "영수증일자")
        record.fields["영수증일자"] = date_field
        record.contract_date = date_field.value

    elif doc_type == DocType.BROKER_RECEIPT:
        fee_field = field_rules.extract_broker_fee(raw_text, file_path)
        record.fields["중개보수"] = fee_field
        date_field = field_rules.extract_date_near_label(
            raw_text, BROKER_DATE_LABELS, file_path, "중개영수증일자")
        record.fields["영수증일자"] = date_field
        record.contract_date = date_field.value

    return record
