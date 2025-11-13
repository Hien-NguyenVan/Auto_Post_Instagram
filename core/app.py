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

        self.title("Instagram Automation Tool")
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

        # Create tab contents and store references for cleanup
        self.users_tab = UsersTab(tab1)
        self.users_tab.pack(fill="both", expand=True)

        self.post_tab = PostTab(tab2)
        self.post_tab.pack(fill="both", expand=True)

        self.follow_tab = FollowTab(tab3)
        self.follow_tab.pack(fill="both", expand=True)

        # Set default tab
        self.tabview.set("👤 Quản lý VM & Tài khoản")

        # ✅ Register cleanup handler khi đóng window
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """
        ✅ Handler khi user đóng window
        Cleanup tất cả tabs trước khi tắt app
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("🚪 USER ĐÓNG APP - BẮT ĐẦU CLEANUP TOÀN BỘ")
        logger.info("=" * 60)

        try:
            # Cleanup PostTab (quan trọng nhất - có threads và VMs)
            if hasattr(self, 'post_tab'):
                logger.info("🔧 Cleanup PostTab...")
                self.post_tab.cleanup()

            # Cleanup FollowTab (nếu có threads)
            if hasattr(self, 'follow_tab') and hasattr(self.follow_tab, 'cleanup'):
                logger.info("🔧 Cleanup FollowTab...")
                self.follow_tab.cleanup()

            # Cleanup UsersTab (nếu cần)
            if hasattr(self, 'users_tab') and hasattr(self.users_tab, 'cleanup'):
                logger.info("🔧 Cleanup UsersTab...")
                self.users_tab.cleanup()

            logger.info("=" * 60)
            logger.info("✅ CLEANUP HOÀN TẤT - ĐÓNG APP")
            logger.info("=" * 60)

        except Exception as e:
            logger.exception(f"❌ Lỗi trong on_closing: {e}")
        finally:
            # Đóng window
            self.destroy()
