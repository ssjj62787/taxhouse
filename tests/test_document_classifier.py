from rtax.extraction.document_classifier import classify
from rtax.models import DocType


def test_classify_notary_receipt():
    assert classify("법무사 수수료 영수증입니다. 취득세 등") == DocType.NOTARY_RECEIPT


def test_classify_broker_receipt():
    assert classify("공인중개사 중개보수 영수증") == DocType.BROKER_RECEIPT


def test_classify_sales_contract():
    assert classify("부동산매매계약서\n매도인과 매수인은...") == DocType.SALES_CONTRACT


def test_classify_auction_cert():
    assert classify("경락대금완납증명원") == DocType.AUCTION_PAYMENT_CERT


def test_classify_unknown():
    assert classify("관련 없는 아무 문서") == DocType.UNKNOWN
