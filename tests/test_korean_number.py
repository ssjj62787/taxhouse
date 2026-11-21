from rtax.extraction.korean_number import parse_korean_amount


def test_arabic_with_won_sign_preferred():
    assert parse_korean_amount("금 삼억오천만원정(₩350,000,000)") == 350_000_000


def test_plain_arabic_amount():
    assert parse_korean_amount("매매대금 700,000,000원") == 700_000_000


def test_hangul_billion_and_ten_million():
    assert parse_korean_amount("일금 칠억이천오백만원정") == 725_000_000


def test_hangul_simple_ten_thousand_unit():
    assert parse_korean_amount("금 십만원") == 100_000


def test_hangul_with_hundred_and_tens():
    assert parse_korean_amount("금 이백삼십사만원") == 2_340_000


def test_unrecognizable_returns_none():
    assert parse_korean_amount("관련 없는 문구입니다") is None


def test_empty_returns_none():
    assert parse_korean_amount("") is None
