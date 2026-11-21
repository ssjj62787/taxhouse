"""전역 설정값. 엔진 교체, 허용 오차 등을 여기서 조정합니다."""
import os

# 추출 엔진: "tesseract" (기본, 로컬 무료) 또는 "claude" (API 키 필요)
OCR_ENGINE = os.environ.get("RTAX_OCR_ENGINE", "tesseract")

# Tesseract 설정
TESSERACT_LANG = "kor+eng"
TESSERACT_CMD = os.environ.get("RTAX_TESSERACT_CMD")  # Windows에서 경로 지정 필요시 사용
TESSERACT_CONFIG = "--psm 6"

# Claude API 설정 (OCR_ENGINE="claude"일 때만 사용)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-5"

# 우리 사업자(매매업자) 명칭 — 매수인/매도인 중 어느 쪽이 우리 쪽인지 자동판별할 때 사용.
# 비워두면 날짜 순서(이른 계약=매수, 늦은 계약=매도)로 추정하고 "검토필요" 플래그를 남김.
CLIENT_BUSINESS_NAME = os.environ.get("RTAX_CLIENT_NAME", "")

# 대조 허용 오차
AMOUNT_TOLERANCE_WON = 1000       # 금액 차이 이 범위 이내면 "일치"로 간주
DATE_TOLERANCE_DAYS = 7           # 날짜 차이 이 범위 이내면 같은 거래로 간주

# 스캔 판별 기준: PDF 페이지에서 뽑힌 글자수가 이 값보다 적으면 "스캔본"으로 보고 OCR 수행
SCANNED_PAGE_TEXT_THRESHOLD = 20

# OCR용 이미지 렌더링 DPI (PDF -> 이미지 변환시)
OCR_RENDER_DPI = 300
