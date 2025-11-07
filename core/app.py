import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tabs.tab_users import UsersTab
from tabs.tab_post import PostTab
from tabs.tab_follow import FollowTab


class App(ttk.Window):
    def __init__(self):
        # Initialize with a modern theme
        # Available themes: cosmo, flatly, litera, minty, lumen, sandstone, yeti, pulse, united, morph, journal, darkly, superhero, solar, cyborg, vapor, simplex, cerculean
        super().__init__(themename="cosmo")

        self.title("Instagram Automation Tool")
        self.geometry("1500x850")

        # Set window icon if available
        # self.iconbitmap("assets/logo.ico")

        # ===================== CUSTOM TREEVIEW STYLE =====================
        style = self.style

        # Tăng độ cao hàng và cỡ chữ
        style.configure(
            "Treeview",
            rowheight=40,  # Tăng chiều cao hàng lên 40px
            font=("Segoe UI", 11),  # Tăng font lên 11
            borderwidth=1,
            relief="solid"
        )

        # Style cho header
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 11, "bold"),  # Font đậm cho header
            borderwidth=1,
            relief="raised"
        )

        # Màu nền xen kẽ và selected
        style.map(
            "Treeview",
            background=[("selected", "#2196F3")],  # Màu xanh khi select
            foreground=[("selected", "white")]
        )

        # Tag cho hàng xen kẽ màu
        # Sẽ được áp dụng trong các tab khi insert rows

        # ===================== CUSTOM BUTTON STYLE =====================
        # Tăng padding và font-weight cho buttons
        style.configure(
            "TButton",
            padding=(12, 8),  # (horizontal, vertical) padding
            font=("Segoe UI", 10, "bold"),
            borderwidth=2,
            relief="raised"
        )

        # Hover effect cho buttons
        style.map(
            "TButton",
            relief=[("pressed", "sunken"), ("active", "raised")],
            borderwidth=[("pressed", 3), ("active", 2)]
        )

        # ===================== CREATE NOTEBOOK =====================
        notebook = ttk.Notebook(self, bootstyle="primary")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Add 3 tabs with icons
        notebook.add(UsersTab(notebook), text="  👤 Quản lý máy ảo & Tài khoản  ")
        notebook.add(PostTab(notebook), text="  📅 Đặt lịch đăng bài  ")
        notebook.add(FollowTab(notebook), text="  ▶️ Theo dõi & Tự động hóa  ")
