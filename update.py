# update.py
import sys
import tkinter as tk
from tkinter import ttk, messagebox

class Updater(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Updater")
        self.geometry("420x200")
        ttk.Label(self, text="Cập nhật công cụ", font=("Segoe UI", 12, "bold")).pack(pady=10)

        self.status = ttk.Label(self, text="Sẵn sàng.")
        self.status.pack(pady=6)

        btns = ttk.Frame(self); btns.pack(pady=10)
        ttk.Button(btns, text="Kiểm tra bản mới", command=self.check_update).pack(side="left", padx=6)
        ttk.Button(btns, text="Tải & cập nhật", command=self.do_update).pack(side="left", padx=6)

    def check_update(self):
        # TODO: gọi API/version.json của bạn
        self.status.config(text="(demo) Chưa cấu hình nguồn cập nhật.")

    def do_update(self):
        # TODO: tải zip, backup, giải nén, thay thế file…
        messagebox.showinfo("Cập nhật", "(demo) Chưa cấu hình logic cập nhật.")

if __name__ == "__main__":
    Updater().mainloop()
