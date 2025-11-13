"""
Instagram post automation module.

Handles automatic Instagram post creation using UIAutomator2.
"""
import time
import uiautomator2 as u2

from utils.base_instagram import BaseInstagramAutomation
from utils.screenshot import take_screenshot
from config import ADB_EXE
from constants import (
    WAIT_SHORT, WAIT_MEDIUM, WAIT_LONG, WAIT_EXTRA_LONG,
    TIMEOUT_DEFAULT, TIMEOUT_APP_OPEN, TIMEOUT_SHORT,
    MAX_RETRY_OPEN_APP, MAX_RETRY_POST_NOTIFICATION, MAX_RETRY_FIND_TAB,
    XPATH_INSTAGRAM_APP, XPATH_FEED_TAB, XPATH_PROMO_BUTTON, XPATH_CREATE_POST,
    XPATH_PROFILE_TAB, XPATH_NEXT_BUTTON, XPATH_RETRY_MEDIA, XPATH_RIGHT_ACTION,
    XPATH_DOWNLOAD_NUX, XPATH_PRIMARY_ACTION, XPATH_CAPTION_INPUT,
    XPATH_ACTION_BAR_TEXT, XPATH_SHARE_BUTTON, XPATH_SHARE_BUTTON_2,XPATH_ALLOW_2, XPATH_CANCEL_BUTTON_ID,
    XPATH_PENDING_MEDIA, XPATH_ACTION_LEFT_CONTAINER,
    CONTENT_DESC_CREATE_NEW, CONTENT_DESC_CREATE_POST,
    CHROME_PACKAGE, INSTAGRAM_PACKAGE, RESOURCE_ID_LEFT_ACTION
)


class InstagramPost(BaseInstagramAutomation):
    """
    Class handles automatic Instagram post creation.

    Inherits from BaseInstagramAutomation for shared functionality.
    """

    def __init__(self, log_callback=None):
        """
        Initialize Instagram post handler.

        Args:
            log_callback: Optional callback function for logging (vm_name, message)
        """
        super().__init__(log_callback)

    def _capture_failure_screenshot(self, adb_address: str, vm_name: str, reason: str):
        """
        Chụp màn hình khi automation thất bại để debug UI changes.

        Args:
            adb_address: ADB device address (e.g., "emulator-5554")
            vm_name: Virtual machine name
            reason: Lý do thất bại (để log)
        """
        try:
            screenshot_path = take_screenshot(adb_address, ADB_EXE, vm_name)
            if screenshot_path:
                self.log(vm_name, f"📸 Screenshot đã lưu: {screenshot_path}")
                self.log(vm_name, f"   💡 Lý do: {reason}")
                self.log(vm_name, f"   🔍 Kiểm tra ảnh để xem Instagram có đổi UI không")
            else:
                self.log(vm_name, "⚠️ Không thể chụp screenshot")
        except Exception as e:
            self.log(vm_name, f"⚠️ Lỗi khi chụp screenshot: {e}")

    def auto_post(self, vm_name: str, adb_address: str, title: str, use_launchex: bool = False,
                  ldconsole_exe: str = None) -> bool:
        """
        Automatically post a video to Instagram.

        Args:
            vm_name: Virtual machine name
            adb_address: ADB address (e.g., emulator-5555)
            title: Post title/caption
            use_launchex: If True, use ldconsole launchex instead of clicking Instagram app
            ldconsole_exe: Path to ldconsole.exe (required if use_launchex=True)

        Returns:
            bool: True if post successful
        """
        d = None
        try:
            self.log(vm_name, f"🔌 Kết nối tới {adb_address}")
            d = u2.connect(adb_address)

            self.log(vm_name, "🔄 Bắt đầu đăng bài...")

            # Open Instagram app
            if use_launchex and ldconsole_exe:
                # Use ldconsole launchex to open Instagram directly
                self.log(vm_name, "📱 Mở ứng dụng Instagram bằng launchex...")
                import subprocess
                try:
                    subprocess.run(
                        [ldconsole_exe, "launchex", "--name", vm_name,
                         "--packagename", "com.instagram.android"],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=10
                    )
                    time.sleep(WAIT_EXTRA_LONG)
                    self.log(vm_name, "✅ Đã mở Instagram app")
                except Exception as e:
                    self.log(vm_name, f"❌ Lỗi mở Instagram bằng launchex: {e}", "ERROR")
                    return False
            else:
                # Original method: click on Instagram app icon
                self.log(vm_name, "📱 Mở ứng dụng Instagram...")
                for i in range(MAX_RETRY_OPEN_APP):
                    if d.xpath(XPATH_INSTAGRAM_APP).exists:
                        if not self.safe_click(d, XPATH_INSTAGRAM_APP, sleep_after=WAIT_EXTRA_LONG, vm_name=vm_name):
                            self.log(vm_name, "❌ Tìm thấy nhưng không click được app Instagram", "ERROR")
                            return False
                        break
                    else:
                        d.app_stop(CHROME_PACKAGE)
                        self.log(vm_name, f"Thử lại lần {i+1}/{MAX_RETRY_OPEN_APP}...")
                        time.sleep(WAIT_SHORT)
                else:
                    self.log(vm_name, f"❌ Không tìm thấy app Instagram sau {MAX_RETRY_OPEN_APP} lần thử", "ERROR")
                    return False

            # Wait for feed tab to appear
            if not self.wait_for_element(d, XPATH_FEED_TAB, timeout=TIMEOUT_APP_OPEN,
                                        vm_name=vm_name, description="feed tab"):
                self.log(vm_name, "❌ Feed tab không xuất hiện", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Feed tab không xuất hiện - Instagram có thể đã đổi giao diện")
                return False

            # Click allow button if exists
            self.log(vm_name, "Nhấn Allow (nếu có)")
            self.safe_click(d, XPATH_PROMO_BUTTON, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT)

            # kiểm tra có create tab hay khong
            if self.wait_for_element(d, XPATH_CREATE_POST,vm_name=vm_name,description="create post", timeout=WAIT_LONG ):
                self.safe_click(d, XPATH_CREATE_POST, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT)
            elif self.wait_for_element(d, XPATH_ACTION_LEFT_CONTAINER,vm_name=vm_name,description="create post", timeout=WAIT_MEDIUM ):
                self.safe_click(d, XPATH_ACTION_LEFT_CONTAINER, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT)
            else:
                # Go to profile tab
                self.log(vm_name, "Chuyển sang tab Profile")
                if not self.safe_click(d, XPATH_PROFILE_TAB, sleep_after=WAIT_LONG, vm_name=vm_name):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Profile", "WARNING")
                    self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy Profile tab - UI có thể đã thay đổi")
                    return False

                self.log(vm_name, "Chuyển sang tab feed tab")
                if not self.safe_click(d, XPATH_FEED_TAB, sleep_after=WAIT_SHORT, vm_name=vm_name):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Profile", "WARNING")
                    return False

                self.log(vm_name, "Chuyển sang tab Profile")
                if not self.safe_click(d, XPATH_PROFILE_TAB, sleep_after=WAIT_MEDIUM, vm_name=vm_name):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Profile", "WARNING")
                    return False

                # Find and click create tab or left button
                self.log(vm_name, "Tìm Create tab hoặc nút trái")
                for i in range(MAX_RETRY_FIND_TAB):
                    creation_tab = d.xpath(CONTENT_DESC_CREATE_NEW).exists
                    action_left = d(resourceId=RESOURCE_ID_LEFT_ACTION).exists

                    if creation_tab:
                        self.log(vm_name, "Nhấn Create tab")
                        if not self.safe_click(d, CONTENT_DESC_CREATE_NEW, sleep_after=WAIT_LONG, vm_name=vm_name):
                            self.log(vm_name, "❌ Không click được Create tab", "ERROR")
                            return False
                        break

                    elif action_left:
                        self.log(vm_name, "Nhấn nút trái")
                        if not self.safe_click(d, XPATH_ACTION_LEFT_CONTAINER, sleep_after=WAIT_LONG, vm_name=vm_name):
                            self.log(vm_name, "❌ Không click được nút trái", "ERROR")
                            return False
                        break

                    time.sleep(WAIT_SHORT)
                else:
                    self.log(vm_name, f"❌ Không tìm thấy Create tab hoặc nút trái sau {MAX_RETRY_FIND_TAB} lần", "ERROR")
                    self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy Create tab - Instagram có thể đã đổi layout")
                    return False

                # Click "Create new post"
                self.log(vm_name, "Nhấn Create new post")
                if not self.safe_click(d, CONTENT_DESC_CREATE_POST, sleep_after=WAIT_LONG, vm_name=vm_name):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Post", "WARNING")
                    self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút Post - Menu có thể đã thay đổi")
                    return False

            # Click Next (top)
            self.log(vm_name, "Nhấn Next (trên)")
            if not self.safe_click(d, XPATH_NEXT_BUTTON, sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "⚠️ Không tìm thấy nút Next trên", "WARNING")
                return False

            # Click Next (bottom)
            self.log(vm_name, "Nhấn Next (dưới)")
            if not self.safe_click(d, XPATH_RIGHT_ACTION, sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "⚠️ Không tìm thấy nút Next dưới", "WARNING")
                return False

            # Click Continue if exists
            self.log(vm_name, "Nhấn Continue (nếu có)")
            self.safe_click(d, XPATH_DOWNLOAD_NUX, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT)

            # Click OK if exists
            self.log(vm_name, "Nhấn OK (nếu có)")
            self.safe_click(d, XPATH_PRIMARY_ACTION, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT)

            # Enter caption
            self.log(vm_name, f"📝 Nhập caption: {title}")
            if not self.safe_send_text(d, XPATH_CAPTION_INPUT, title,
                                      sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "❌ Không thể nhập caption", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy caption input - UI có thể đã thay đổi")
                return False

            # Click OK button
            self.log(vm_name, "🔑 Nhấn OK")
            if not self.safe_click(d, XPATH_ACTION_BAR_TEXT, sleep_after=WAIT_LONG, vm_name=vm_name):
                self.log(vm_name, "❌ Không tìm thấy nút OK", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút OK sau nhập caption")
                return False

            # Click Share
            self.log(vm_name, "🔑 Nhấn Share")
            if not self.safe_click(d, XPATH_SHARE_BUTTON, sleep_after=WAIT_SHORT, vm_name=vm_name, timeout=2):
                self.log(vm_name, "❌ Không tìm thấy nút Share", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút Share - UI upload có thể đã thay đổi")
                return False

            # Click allow 
            self.log(vm_name, "🔑 Nhấn allow")
            self.safe_click(d, XPATH_ALLOW_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)
            # Click Share 2
            self.log(vm_name, "🔑 Nhấn Share 2")
            self.safe_click(d, XPATH_SHARE_BUTTON_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)
            
            # Click Share 3
            self.log(vm_name, "🔑 Nhấn Share 3")
            self.safe_click(d, XPATH_SHARE_BUTTON_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)
            # Click allow 
            self.log(vm_name, "🔑 Nhấn allow")
            self.safe_click(d, XPATH_ALLOW_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)

            # Click "No thanks" if exists
            self.log(vm_name, "🔑 Nhấn No thanks (nếu có)")
            self.safe_click(d, XPATH_CANCEL_BUTTON_ID, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=3)

            # Wait for post notification
            self.log(vm_name, "⏳ Chờ đăng bài...")
            for i in range(MAX_RETRY_POST_NOTIFICATION):
                if d.xpath(XPATH_PENDING_MEDIA).exists:
                    self.log(vm_name, "✅ Đã có thông báo đăng bài!")
                    break
                
                if d.xpath(XPATH_RETRY_MEDIA).exists:
                    self.log(vm_name, "❌ Đăng không thành công - Instagram từ chối post")
                    self._capture_failure_screenshot(adb_address, vm_name, "Instagram từ chối đăng bài - Có thể video vi phạm guidelines hoặc UI thay đổi")
                    return False

                time.sleep(WAIT_SHORT)
            else:
                self.log(vm_name, "⚠️ Không thấy thông báo đăng bài, nhưng có thể đã post thành công", "WARNING")

            time.sleep(WAIT_MEDIUM)
            return True

        except Exception as e:
            self.log(vm_name, f"❌ Lỗi tự động đăng bài: {e}", "ERROR")
            self.logger.exception("Exception in auto_post")
            return False

        finally:
            # Always try to close app
            if d:
                try:
                    d.app_stop(INSTAGRAM_PACKAGE)
                    self.log(vm_name, "🛑 Đã đóng Instagram app")
                except Exception as e:
                    self.logger.warning(f"Failed to close Instagram app: {e}")
