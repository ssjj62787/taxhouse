# Windows에서 exe 빌드하기

PyInstaller는 "지금 실행 중인 OS용" 실행파일만 만듭니다. 그래서 Windows용 exe는
반드시 Windows PC에서 빌드해야 합니다 (macOS/Linux에서는 만들 수 없습니다).

## 1. Python 설치 확인
- https://www.python.org/downloads/ 에서 3.10 이상 설치 (설치 시 "Add to PATH" 체크)

## 2. Tesseract-OCR 설치 (OCR 기본 엔진)
- https://github.com/UB-Mannheim/tesseract/wiki 에서 Windows 설치파일 다운로드
- 설치 중 "Additional language data" → **Korean** 체크 (한글 인식을 위해 필수)
- 설치 경로를 기억해 두세요. 보통:
  `C:\Program Files\Tesseract-OCR\tesseract.exe`

> 이 설치는 **exe를 실행할 모든 팀원 PC에 1회씩 필요**합니다. exe 자체에는
> Tesseract 바이너리를 포함하지 않았습니다 (별도 설치형 프로그램이라 파이썬
> 패키지처럼 묶기 어렵고, 또 라이선스/업데이트 관리 측면에서도 독립 설치가 낫습니다).

## 3. 프로젝트 내려받기 & 의존성 설치
```powershell
git clone https://github.com/ssjj62787/taxhouse.git
cd taxhouse
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 4. tesseract 경로 지정 (PATH에 없다면)
`rtax/config.py` 에서:
```python
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```
또는 실행 전 환경변수로:
```powershell
$env:RTAX_TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 5. 동작 확인 (exe 빌드 전에 먼저 GUI로 테스트)
```powershell
python main.py
```

## 6. exe 빌드
```powershell
pyinstaller build\app.spec
```
빌드가 끝나면 `dist\RealEstateTaxAssistant.exe` 가 생성됩니다.
이 파일 하나만 팀원들에게 공유하면 되고, 각 팀원 PC에는 2번(Tesseract-OCR)만
설치되어 있으면 됩니다.

## 7. (선택) GitHub Actions로 자동 빌드
팀원이 코드를 바꿀 때마다 수동으로 Windows PC에서 빌드하기 번거롭다면,
`windows-latest` 러너를 쓰는 GitHub Actions 워크플로를 추가해 push할 때마다
자동으로 exe를 만들어 Actions 아티팩트로 올려주는 방식도 가능합니다.
필요하시면 `.github/workflows/build-exe.yml` 을 추가해 드릴게요.
