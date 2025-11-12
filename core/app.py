import customtkinter as ctk
from tkinter import ttk  # For Treeview styling
from ui_theme import *

from tabs.tab_users import UsersTab
from tabs.tab_post import PostTab
from tabs.tab_follow import FollowTab


class App(ctk.CTk):
    """Main Application Window - Modern Windows 11 Style"""

    def __init__(self):
        super().__init__()

        # Apply Windows 11 theme
        apply_ctk_theme()
        self.configure(fg_color=COLORS["bg_primary"])

        self.title("Instagram Automation Tool - Windows 11 Style")
        self.geometry("1600x900")

        # Set minimum window size
        self.minsize(1200, 700)

        # Set window icon if available
        # self.iconbitmap("assets/logo.ico")

        # ===================== TREEVIEW STYLE (for tables in tabs) =====================
        style = ttk.Style()
        style.theme_use("clam")

        # Global Treeview style
        style.configure(
            "Treeview",
            rowheight=40,
            font=(FONTS["family"], FONTS["size_normal"]),
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_secondary"],
            borderwidth=0
        )

        # Treeview heading style
        style.configure(
            "Treeview.Heading",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            background=COLORS["surface_3"],
            foreground=COLORS["text_primary"],
            borderwidth=1,
            relief="flat"
        )

        # Treeview selection color
        style.map(
            "Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["text_on_accent"])]
        )

        # ===================== CREATE TABVIEW =====================
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=DIMENSIONS["corner_radius_large"],
            fg_color=COLORS["bg_secondary"],
            segmented_button_fg_color=COLORS["surface_1"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["surface_2"],
            segmented_button_unselected_hover_color=COLORS["surface_3"],
            text_color=COLORS["text_primary"],
            text_color_disabled=COLORS["disabled"]
        )
        self.tabview.pack(fill="both", expand=True, padx=DIMENSIONS["spacing_lg"], pady=DIMENSIONS["spacing_lg"])

        # Add 3 tabs with icons
        tab1 = self.tabview.add("👤 Quản lý VM & Tài khoản")
        tab2 = self.tabview.add("📅 Đặt lịch đăng bài")
        tab3 = self.tabview.add("▶️ Theo dõi & Tự động")

        # Create tab contents
        UsersTab(tab1).pack(fill="both", expand=True)
        PostTab(tab2).pack(fill="both", expand=True)
        FollowTab(tab3).pack(fill="both", expand=True)

        # Set default tab
        self.tabview.set("👤 Quản lý VM & Tài khoản")
