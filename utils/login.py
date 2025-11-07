"""
Instagram login automation module.

Handles automatic Instagram login with 2FA support using UIAutomator2.
"""
import time
import re
import os
import json
import requests
import uiautomator2 as u2

from utils.base_instagram import BaseInstagramAutomation
from constants import (
    WAIT_SHORT, WAIT_MEDIUM, WAIT_LONG, WAIT_EXTRA_LONG,
    TIMEOUT_DEFAULT, TIMEOUT_SHORT, TIMEOUT_MEDIUM,
    XPATH_INSTAGRAM_APP, XPATH_ALREADY_HAVE_ACCOUNT,
    XPATH_USERNAME_INPUT, XPATH_PASSWORD_INPUT, XPATH_LOGIN_BUTTON,
    XPATH_TRY_ANOTHER_WAY, XPATH_AUTH_APP, XPATH_CONTINUE_BUTTON,
    XPATH_CODE_INPUT, XPATH_SAVE_BUTTON, XPATH_SKIP_BUTTON,
    XPATH_DENY_BUTTON, XPATH_CANCEL_BUTTON, XPATH_PROFILE_TAB,
    XPATH_PROFILE_NAME, CHROME_PACKAGE, CHROME_TITLE_ID,
    INSTAGRAM_PACKAGE, TWOFA_API_URL
)


class InstagramLogin(BaseInstagramAutomation):
    """
    Class handles automatic Instagram login process.

    Inherits from BaseInstagramAutomation for shared functionality.
    """

    def __init__(self, log_callback=None):
        """
        Initialize Instagram login handler.

        Args:
            log_callback: Optional callback function for logging (vm_name, message)
        """
        super().__init__(log_callback)

    def get_2fa_code(self, key_2fa: str) -> str:
        """
        Get 2FA code from API.

        Args:
            key_2fa: 2FA key (may contain spaces)

        Returns:
            str: 2FA code or None if error
        """
        try:
            # Remove spaces and convert to uppercase
            key = re.sub(r'\s+', '', key_2fa).upper()
            url = TWOFA_API_URL.format(key=key)

            r = requests.get(url, timeout=8)
            data = r.json()
            code = data.get("token", "")

            if not code or code == "No token":
                self.logger.error(f"No token received from 2FA API for key: {key[:10]}...")
                return None

            return code

        except requests.RequestException as e:
            self.logger.error(f"Request error calling 2FA API: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"Error calling 2FA API: {e}")
            return None

    def auto_login(self, vm_name: str, adb_address: str, username: str,
                   password: str, key_2fa: str) -> bool:
        """
        Automatically login to Instagram with 2FA.

        Args:
            vm_name: Virtual machine name
            adb_address: ADB address (e.g., emulator-5555)
            username: Instagram username
            password: Instagram password
            key_2fa: 2FA key

        Returns:
            bool: True if login successful
        """
        d = None
        try:
            self.log(vm_name, f"🔌 Kết nối tới {adb_address}")
            d = u2.connect(adb_address)

            self.log(vm_name, "🔄 Bắt đầu đăng nhập...")

            # Close Chrome if it's showing Google screen
            try:
                if d(resourceId=CHROME_TITLE_ID).exists:
                    d.app_stop(CHROME_PACKAGE)
                    self.log(vm_name, f"Đã đóng {CHROME_PACKAGE}")
                    time.sleep(WAIT_SHORT)
            except Exception as e:
                self.logger.warning(f"Error checking/closing Chrome: {e}")

            # Open Instagram app
            self.log(vm_name, "📱 Mở ứng dụng Instagram...")
            if not self.safe_click(d, XPATH_INSTAGRAM_APP, sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "❌ Không tìm thấy app Instagram", "ERROR")
                return False

            # Click "I already have an account" (optional - may not appear)
            self.log(vm_name, "👤 Chọn 'I already have an account'...")
            self.safe_click(d, XPATH_ALREADY_HAVE_ACCOUNT, sleep_after=WAIT_MEDIUM,
                          vm_name=vm_name, optional=True)

            # Enter username
            self.log(vm_name, f"📝 Nhập username: {username}")
            if not self.safe_send_text(d, XPATH_USERNAME_INPUT, username,
                                      sleep_after=4, vm_name=vm_name):
                self.log(vm_name, "❌ Không thể nhập username", "ERROR")
                return False

            # Enter password
            self.log(vm_name, "🔐 Nhập password")
            if not self.safe_send_text(d, XPATH_PASSWORD_INPUT, password,
                                      sleep_after=WAIT_SHORT, vm_name=vm_name):
                self.log(vm_name, "❌ Không thể nhập password", "ERROR")
                return False

            # Click Log in
            self.log(vm_name, "🔑 Nhấn Log in...")
            if not self.safe_click(d, XPATH_LOGIN_BUTTON, sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "❌ Không tìm thấy nút Log in", "ERROR")
                return False

            # Click "Try another way"
            self.log(vm_name, "🔄 Chọn Try another way...")
            if not self.safe_click(d, XPATH_TRY_ANOTHER_WAY, sleep_after=WAIT_SHORT, vm_name=vm_name):
                self.log(vm_name, "❌ Không tìm thấy nút Try another way", "ERROR")
                return False

            # Select "Authentication app"
            self.log(vm_name, "📱 Chọn Authentication app...")
            if not self.safe_click(d, XPATH_AUTH_APP, sleep_after=WAIT_SHORT, vm_name=vm_name):
                self.log(vm_name, "❌ Không tìm thấy 'Authentication app'", "ERROR")
                return False

            # Click Continue
            if not self.safe_click(d, XPATH_CONTINUE_BUTTON, sleep_after=WAIT_MEDIUM, vm_name=vm_name):
                self.log(vm_name, "⚠️ Không tìm thấy nút Continue", "WARNING")
                return False

            # Get 2FA code
            self.log(vm_name, "🔒 Đang lấy mã 2FA...")
            code = self.get_2fa_code(key_2fa)

            if not code:
                self.log(vm_name, f"❌ Không lấy được mã 2FA từ key: {key_2fa[:10]}...", "ERROR")
                return False

            self.log(vm_name, f"✅ Đã lấy mã 2FA: {code}")

            # Enter 2FA code
            self.log(vm_name, "📝 Nhập mã 2FA...")
            if not self.safe_send_text(d, XPATH_CODE_INPUT, code, sleep_after=WAIT_SHORT, vm_name=vm_name):
                self.log(vm_name, "❌ Không thể nhập mã 2FA", "ERROR")
                return False

            # Click Continue again
            self.log(vm_name, "▶️ Nhấn Continue...")
            if not self.safe_click(d, XPATH_CONTINUE_BUTTON, sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "⚠️ Không tìm thấy nút Continue", "WARNING")
                return False

            # Click Save (optional)
            self.log(vm_name, "💾 Lưu thông tin đăng nhập...")
            if not self.safe_click(d, XPATH_SAVE_BUTTON, sleep_after=WAIT_SHORT,
                                  vm_name=vm_name, optional=True, timeout=TIMEOUT_MEDIUM):
                self.log(vm_name, "✅ Hoàn tất đăng nhập (không có nút Save)")
                # Continue to next step even if Save button not found
            else:
                self.log(vm_name, "✅ Hoàn tất đăng nhập!")

            # Skip setup screens
            self.log(vm_name, "⏳ Bỏ qua màn hình setup...")
            if self.safe_click(d, XPATH_SKIP_BUTTON, sleep_after=3, vm_name=vm_name,
                             optional=True, timeout=TIMEOUT_SHORT):
                # After Skip, handle location prompts
                self.safe_click(d, XPATH_CONTINUE_BUTTON, sleep_after=3, vm_name=vm_name,
                              optional=True, timeout=TIMEOUT_SHORT)
                self.safe_click(d, XPATH_DENY_BUTTON, sleep_after=3, vm_name=vm_name,
                              optional=True, timeout=TIMEOUT_SHORT)
                self.safe_click(d, XPATH_CANCEL_BUTTON, vm_name=vm_name,
                              optional=True, timeout=TIMEOUT_SHORT)

            # Get Instagram account name
            self.log(vm_name, "📝 Lấy tên tài khoản Instagram")
            if not self.safe_click(d, XPATH_PROFILE_TAB, sleep_after=WAIT_SHORT,
                                  vm_name=vm_name, timeout=TIMEOUT_SHORT):
                self.log(vm_name, "⚠️ Không tìm thấy nút Profile", "WARNING")
            else:
                el = d.xpath(XPATH_PROFILE_NAME)
                if el.exists:
                    text_value = el.get_text()
                    self.log(vm_name, f"Tên tài khoản: {text_value}")

                    # Update JSON file with Instagram name
                    self._save_insta_name(vm_name, text_value)
                else:
                    self.log(vm_name, "Không tìm thấy tên tài khoản", "WARNING")

            # Wait and close app
            self.log(vm_name, "✅ Chờ 5s trước khi kết thúc...")
            time.sleep(WAIT_MEDIUM)
            d.app_stop(INSTAGRAM_PACKAGE)
            self.log(vm_name, "🛑 Đóng ứng dụng Instagram")
            return True

        except Exception as e:
            self.log(vm_name, f"❌ Lỗi tự động đăng nhập: {e}", "ERROR")
            self.logger.exception("Exception in auto_login")

            # Try to close app on error
            if d:
                try:
                    d.app_stop(INSTAGRAM_PACKAGE)
                    self.log(vm_name, "🛑 Đóng ứng dụng Instagram (sau lỗi)")
                except Exception:
                    pass

            return False

    def _save_insta_name(self, vm_name: str, insta_name: str) -> bool:
        """
        Save Instagram name to VM JSON file.

        Args:
            vm_name: VM name
            insta_name: Instagram account name

        Returns:
            bool: True if saved successfully
        """
        path = os.path.join("data", f"{vm_name}.json")
        try:
            with open(path, "r", encoding="utf-8") as fp:
                file_data = json.load(fp)

            file_data["insta_name"] = insta_name

            with open(path, "w", encoding="utf-8") as fp:
                json.dump(file_data, fp, ensure_ascii=False, indent=2)

            self.log(vm_name, f"💾 Đã lưu insta_name vào {path}")
            return True

        except Exception as e:
            self.log(vm_name, f"⚠️ Lỗi khi lưu insta_name: {e}", "ERROR")
            self.logger.exception(f"Error saving insta_name to {path}")
            return False
