# 부동산 매매업 세무회계 처리 도구 (taxhouse)

부동산 매매(법인/개인) 증빙 PDF·사진과 위하고(WEHAGO) 자동전표를 입력받아,
① 토지등 매매차익 예정신고서 작성용 기초 데이터, ② 위하고 전표 대조 결과,
③ 주소지 거래처 기준 분개 초안을 5개 섹션 리포트 + xlsx 파일로 만들어 줍니다.

> **원칙**: 라벨(계약일/매매대금/취득세 등) 주변에서만 값을 추출하고, 판독이
> 불명확하거나 누락된 항목은 절대 추정하지 않고 `[미확인/누락]`으로 남깁니다.
> 역할 판단이 애매한 부분(매수/매도 계약서 구분, 계정과목, 부가세 공제 여부)은
> 전부 리포트의 "세무대리인 최종 확인 사항"에 근거와 함께 표시됩니다.

## 빠른 시작

```bash
pip install -r requirements.txt
pytest tests/ -v                     # 핵심 로직 단위테스트 (OCR 없이도 실행됨)

python main.py                       # GUI 실행
# 또는
python -m rtax.cli --case-dir <증빙폴더> --wehago <위하고파일> --out result.xlsx
```

Windows에서 exe로 패키징해 팀원들과 공유하는 방법은 [`build/BUILD_WINDOWS.md`](build/BUILD_WINDOWS.md) 참고.

## 구조

```
rtax/
  config.py              전역 설정 (OCR 엔진 선택, 허용오차 등)
  models.py              공용 데이터 모델
  engines/               OCR 엔진 (tesseract 기본, claude 선택형) — 모듈 교체 가능
  ingest/                PDF/사진 읽기, 전처리(기울기보정 등), 폴더 단위 로딩
  extraction/            라벨 기반 항목 추출, 문서 분류, 건(Case) 단위 조립
  wehago/                위하고 전표(xlsx/csv) 로딩
  matching/              증빙 vs 전표 대조(reconciler)
  journal/                계정과목 매핑 + 분개초안 생성
  reporting/              텍스트 리포트 + xlsx 리포트 생성
  gui/app.py              Tkinter GUI (exe 빌드 대상)
  cli.py                  커맨드라인 실행
  pipeline.py             전체 흐름 오케스트레이션
build/                   PyInstaller 스펙, Windows 빌드 안내
sample_data/              샘플 위하고 전표 + 테스트 절차 안내
tests/                    단위테스트 (한글금액 변환, 라벨추출, 대조, 분개 등)
```

## OCR 엔진 교체

기본값은 로컬 무료 **Tesseract**입니다. 사진이 많이 기울어지거나 반사·흐림이
심해서 정확도가 아쉬우면, Anthropic API 키가 있을 때 Claude 멀티모달로 바꿀 수
있습니다 (비용 발생):

```bash
export ANTHROPIC_API_KEY=sk-...
export RTAX_OCR_ENGINE=claude
```

| 엔진 | 비용 | 설치 난이도 | 기울기/반사/흐림 내구성 | 한글 손글씨·도장 |
|---|---|---|---|---|
| Tesseract (기본) | 무료 | 중 (별도 바이너리 설치 필요) | 낮음 — 전처리로 일부 보완 | 약함 |
| Claude API | 사용량 과금 | 낮음 (pip만) | 높음 | 비교적 강함 |

## 알려진 한계 (v1)

- 매수계약서/매도계약서, 매수/매도 중개사영수증처럼 "같은 양식, 다른 역할" 증빙은
  **계약일(영수증일자) 순서로 자동 판단**합니다 — 날짜 추출이 잘못되면 역할도
  잘못 배정될 수 있어 항상 리포트 [5]번 섹션에 확인 플래그를 남깁니다.
- 위하고 전표 대조는 금액·날짜 기준이며, 정확히 일치하는 금액을 최우선으로
  전역 배정한 뒤 남은 항목만 날짜 근접도로 "불일치" 후보를 찾습니다 — 금액도
  날짜도 안 맞으면 억지로 엮지 않고 "누락"으로 둡니다.
- 계정과목(재고자산 vs 비용, 부가세 공제 여부)은 최종 판단하지 않고 선택지와
  "세무사 확인 필요" 메모만 남깁니다.
