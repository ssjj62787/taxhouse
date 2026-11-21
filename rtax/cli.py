"""CLI 실행: python -m rtax.cli --case-dir ... --wehago ... --out ..."""
import argparse

from rtax.pipeline import run_case


def main():
    parser = argparse.ArgumentParser(description="부동산 매매업 세무회계 처리 도구")
    parser.add_argument("--case-dir", required=True, help="증빙 PDF/사진이 들어있는 폴더")
    parser.add_argument("--wehago", required=False, default=None, help="위하고 전표 xlsx/csv 경로")
    parser.add_argument("--out", required=True, help="결과 xlsx 저장 경로")
    parser.add_argument("--case-id", required=False, default=None, help="물건 식별자(기본: 폴더명)")
    args = parser.parse_args()

    report = run_case(
        case_dir=args.case_dir,
        wehago_path=args.wehago,
        out_xlsx_path=args.out,
        case_id=args.case_id,
        progress_cb=print,
    )
    print()
    print(report)


if __name__ == "__main__":
    main()
