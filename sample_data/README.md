# 샘플 테스트 절차

실제 증빙 없이도 핵심 로직(한글 금액 변환, 라벨 추출, 대조, 분개 생성)은
`tests/` 아래 단위테스트로 바로 확인할 수 있습니다.

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## 실제 파일로 끝까지 테스트해보기

1. 증빙 폴더를 하나 만들고(예: `sample_data/case1/`) 매수계약서/법무사영수증/
   중개사영수증/매도계약서 PDF 또는 사진을 넣습니다.
2. 이 폴더의 `sample_wehago_ledger.csv` 를 참고해서 실제 위하고 전표를 내려받습니다
   (일자/적요/거래처/공급가액/부가세/합계 컬럼이 있으면 자동으로 인식됩니다).
3. CLI로 실행:
   ```bash
   python -m rtax.cli --case-dir sample_data/case1 --wehago sample_data/sample_wehago_ledger.csv --out sample_data/case1_result.xlsx
   ```
   또는 GUI(`python main.py`)에서 폴더/파일을 선택 후 "실행" 클릭.
4. 결과 xlsx와 콘솔에 출력되는 5단 리포트를 확인합니다.
   `[미확인/누락]`으로 표시된 항목은 원문 PDF를 직접 보고 세무대리인이 채워야 하는 부분입니다.
