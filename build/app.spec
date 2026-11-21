# PyInstaller 스펙 파일. 프로젝트 루트에서 아래처럼 실행하면 exe가 생성됩니다:
#   pyinstaller build/app.spec
# (반드시 Windows에서 실행해야 Windows용 exe가 나옵니다 — PyInstaller는 교차 컴파일을 지원하지 않습니다.)
import os

ROOT = os.path.join(SPECPATH, "..")
block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=["PIL._tkinter_finder"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onefile 빌드: COLLECT 단계 없이 EXE에 binaries/zipfiles/datas를 바로 포함시키면
# 실행파일 하나로 패키징됩니다 (`pyinstaller --onefile`과 동일한 구조).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RealEstateTaxAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
