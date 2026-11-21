"""공용 데이터 모델. 모든 모듈이 이 구조로 데이터를 주고받습니다."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class DocType(str, Enum):
    SALES_CONTRACT = "매매계약서"                 # 매수/매도 역할은 case_builder가 날짜로 판단
    AUCTION_PAYMENT_CERT = "경락대금완납증명원"
    NOTARY_RECEIPT = "법무사영수증"
    BROKER_RECEIPT = "중개사영수증"                # 매수/매도 역할은 case_builder가 판단
    WEHAGO_LEDGER = "위하고전표"
    UNKNOWN = "미분류"


REQUIRED_SLOTS = [
    "매수계약서(또는 경락대금완납증명원)",
    "법무사영수증",
    "매수시 중개사영수증",
    "매도계약서",
    "매도시 중개사영수증",
]


@dataclass
class Evidence:
    source_file: str
    snippet: str


@dataclass
class ExtractedField:
    label: str
    value: Optional[Any] = None
    confidence: str = "확인"          # "확인" | "검토필요" | "미확인/누락"
    evidence: Optional[Evidence] = None
    note: str = ""


@dataclass
class DocumentRecord:
    file_path: str
    doc_type: DocType
    raw_text: str
    contract_date: Optional[str] = None   # 역할(매수/매도) 판별용으로 뽑아둔 대표 날짜
    fields: Dict[str, ExtractedField] = field(default_factory=dict)


@dataclass
class CaseData:
    case_id: str
    address: Optional[ExtractedField] = None
    property_type: Optional[ExtractedField] = None
    area: Optional[ExtractedField] = None

    purchase_contract_date: Optional[ExtractedField] = None
    acquisition_date: Optional[ExtractedField] = None     # 잔금청산일/등기접수일
    sale_contract_date: Optional[ExtractedField] = None
    transfer_date: Optional[ExtractedField] = None        # 양도일(잔금청산일 등)

    transfer_price: Optional[ExtractedField] = None       # 양도가액
    acquisition_price: Optional[ExtractedField] = None    # 취득가액(매수대금/경락대금)

    notary_items: List[ExtractedField] = field(default_factory=list)
    broker_fee_buy: Optional[ExtractedField] = None
    broker_fee_sell: Optional[ExtractedField] = None

    documents: List[DocumentRecord] = field(default_factory=list)
    missing_docs: List[str] = field(default_factory=list)
    review_notes: List[str] = field(default_factory=list)


@dataclass
class LedgerEntry:
    date: Optional[str]
    description: str
    counterparty: Optional[str]
    supply_amount: Optional[float]
    vat_amount: Optional[float]
    total_amount: Optional[float]
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchResult:
    label: str
    evidence_amount: Optional[float]
    ledger_amount: Optional[float]
    date: Optional[str]
    counterparty: str
    status: str   # "일치" | "불일치" | "누락(전표 미입력)" | "누락(증빙 미확보)"
    note: str = ""


@dataclass
class JournalLine:
    debit_account: str
    credit_account: str
    counterparty: str
    amount: Optional[float]
    description: str
    status: str            # "일치" | "수정필요" | "신규입력"
    review_note: str = ""
