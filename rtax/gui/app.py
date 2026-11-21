"""간단한 로컬 GUI. exe로 패키징했을 때 팀원들이 더블클릭만으로 쓰도록 Tkinter 사용
(추가 설치 없이 Python에 기본 포함되는 라이브러리라서 PyInstaller exe 용량도 작게 유지됩니다)."""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from rtax.pipeline import run_case


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("부동산 매매업 세무회계 도우미")
        self.geometry("760x560")

        self.case_dir_var = tk.StringVar()
        self.wehago_var = tk.StringVar()
        self.out_var = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self):
        pad = {"padx": 8, "pady": 6}

        row1 = tk.Frame(self)
        row1.pack(fill="x", **pad)
        tk.Label(row1, text="① 증빙 폴더(PDF/사진)", width=22, anchor="w").pack(side="left")
        tk.Entry(row1, textvariable=self.case_dir_var).pack(side="left", fill="x", expand=True)
        tk.Button(row1, text="선택", command=self._pick_case_dir).pack(side="left", padx=4)

        row2 = tk.Frame(self)
        row2.pack(fill="x", **pad)
        tk.Label(row2, text="② 위하고 전표(xlsx/csv)", width=22, anchor="w").pack(side="left")
        tk.Entry(row2, textvariable=self.wehago_var).pack(side="left", fill="x", expand=True)
        tk.Button(row2, text="선택", command=self._pick_wehago).pack(side="left", padx=4)

        row3 = tk.Frame(self)
        row3.pack(fill="x", **pad)
        tk.Label(row3, text="③ 결과 저장 경로(xlsx)", width=22, anchor="w").pack(side="left")
        tk.Entry(row3, textvariable=self.out_var).pack(side="left", fill="x", expand=True)
        tk.Button(row3, text="선택", command=self._pick_out).pack(side="left", padx=4)

        row4 = tk.Frame(self)
        row4.pack(fill="x", **pad)
        self.run_btn = tk.Button(row4, text="실행", command=self._run_clicked, bg="#1F4E78", fg="white")
        self.run_btn.pack(side="left")

        self.log_box = scrolledtext.ScrolledText(self, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)

    def _pick_case_dir(self):
        path = filedialog.askdirectory(title="증빙 폴더 선택")
        if path:
            self.case_dir_var.set(path)
            if not self.out_var.get():
                default_out = os.path.join(path, "매매차익_위하고_분개초안.xlsx")
                self.out_var.set(default_out)

    def _pick_wehago(self):
        path = filedialog.askopenfilename(
            title="위하고 전표 파일 선택",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("모든 파일", "*.*")],
        )
        if path:
            self.wehago_var.set(path)

    def _pick_out(self):
        path = filedialog.asksaveasfilename(
            title="결과 저장 위치", defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
        )
        if path:
            self.out_var.set(path)

    def _log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    def _run_clicked(self):
        case_dir = self.case_dir_var.get().strip()
        out_path = self.out_var.get().strip()
        if not case_dir or not os.path.isdir(case_dir):
            messagebox.showerror("오류", "증빙 폴더를 올바르게 선택해 주세요.")
            return
        if not out_path:
            messagebox.showerror("오류", "결과 저장 경로를 지정해 주세요.")
            return

        self.run_btn.config(state="disabled")
        self.log_box.delete("1.0", "end")
        wehago_path = self.wehago_var.get().strip() or None

        def worker():
            try:
                report = run_case(
                    case_dir=case_dir, wehago_path=wehago_path,
                    out_xlsx_path=out_path, progress_cb=self._log,
                )
                self._log("\n" + report)
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{out_path}")
            except Exception as e:  # noqa: BLE001
                self._log(f"[오류] {e}")
                messagebox.showerror("오류", str(e))
            finally:
                self.run_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
