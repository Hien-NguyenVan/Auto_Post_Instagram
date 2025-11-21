"""
Instagram post automation module.

Handles automatic Instagram post creation using UIAutomator2.
"""
import time
import subprocess
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
    XPATH_ACTION_BAR_TEXT, XPATH_SHARE_BUTTON, XPATH_SHARE_BUTTON_2,XPATH_ALLOW_2, XPATH_CANCEL_BUTTON_ID,XPATH_SHARE_TO,XPATH_NOT_SHARE,
    XPATH_PENDING_MEDIA, XPATH_ACTION_LEFT_CONTAINER,XPATH_POST,XPATH_FIRST_BOX,XPATH_progress_bar,
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

    def _retry_mediastore_broadcast(self, adb_address: str, video_filename: str, vm_name: str, max_retries: int = 3):
        """
        Retry broadcast MediaStore để Gallery/Instagram nhận ra file.

        Strategy:
        - Lần 1-2: Scan file cụ thể
        - Lần 3: Scan toàn bộ DCIM folder (force full refresh)

        Args:
            adb_address: ADB device address (e.g., "emulator-5554")
            video_filename: Video filename (e.g., 'video.mp4')
            vm_name: Virtual machine name
            max_retries: Maximum number of retries (default: 3)

        Returns:
            bool: True if broadcast successful
        """
        if not video_filename:
            self.log(vm_name, "⚠️ Không có video_filename để retry broadcast")
            return False

        remote_path = f"/sdcard/DCIM/{video_filename}"

        for attempt in range(1, max_retries + 1):
            try:
                # ✅ v1.5.32: Lần cuối cùng scan toàn bộ DCIM folder thay vì từng file
                if attempt == max_retries:
                    self.log(vm_name, f"🔁 Retry {attempt}/{max_retries}: Scan toàn bộ DCIM folder...")
                    # Scan entire DCIM folder
                    subprocess.run([
                        ADB_EXE, "-s", adb_address, "shell",
                        "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                        "-d", "file:///sdcard/DCIM"
                    ],
                    capture_output=True, text=True, encoding="utf-8", errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=15  # Timeout lâu hơn cho folder scan
                    )
                else:
                    self.log(vm_name, f"🔁 Retry {attempt}/{max_retries}: Scan file {video_filename}...")
                    # Scan specific file
                    subprocess.run([
                        ADB_EXE, "-s", adb_address, "shell",
                        "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                        "-d", f"file://{remote_path}"
                    ],
                    capture_output=True, text=True, encoding="utf-8", errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                    )

                self.log(vm_name, f"✅ Đã broadcast MediaStore (lần {attempt})")
                time.sleep(3)  # Tăng từ 2s lên 3s để đợi MediaStore update
                return True
            except Exception as e:
                self.log(vm_name, f"⚠️ Lỗi retry broadcast (lần {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(1)

        return False

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
                  ldconsole_exe: str = None, video_filename: str = None) -> bool:
        """
        Automatically post a video to Instagram.

        Args:
            vm_name: Virtual machine name
            adb_address: ADB address (e.g., emulator-5555)
            title: Post title/caption
            use_launchex: If True, use ldconsole launchex instead of clicking Instagram app
            ldconsole_exe: Path to ldconsole.exe (required if use_launchex=True)
            video_filename: Video filename (e.g., 'video.mp4') for MediaStore broadcast retry

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
                        if not self.safe_click(d, XPATH_INSTAGRAM_APP, sleep_after=WAIT_EXTRA_LONG,
                                              vm_name=vm_name, description="Instagram app icon"):
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
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT,
                          description="Allow button")

            # kiểm tra có create tab hay khong
            if self.wait_for_element(d, XPATH_CREATE_POST,vm_name=vm_name,description="create post", timeout=WAIT_LONG ):
                self.safe_click(d, XPATH_CREATE_POST, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT,
                          description="Create post button")
            elif self.wait_for_element(d, XPATH_ACTION_LEFT_CONTAINER,vm_name=vm_name,description="create post", timeout=WAIT_MEDIUM ):
                self.safe_click(d, XPATH_ACTION_LEFT_CONTAINER, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT,
                          description="Action left button")
            else:
                # Go to profile tab
                self.log(vm_name, "Chuyển sang tab Profile")
                if not self.safe_click(d, XPATH_PROFILE_TAB, sleep_after=WAIT_LONG,
                                      vm_name=vm_name, description="Profile tab"):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Profile", "WARNING")
                    self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy Profile tab - UI có thể đã thay đổi")
                    return False

                self.log(vm_name, "Chuyển sang tab feed tab")
                if not self.safe_click(d, XPATH_FEED_TAB, sleep_after=WAIT_SHORT,
                                      vm_name=vm_name, description="Feed tab"):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Feed", "WARNING")
                    return False

                self.log(vm_name, "Chuyển sang tab Profile")
                if not self.safe_click(d, XPATH_PROFILE_TAB, sleep_after=WAIT_MEDIUM,
                                      vm_name=vm_name, description="Profile tab"):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Profile", "WARNING")
                    return False

                # Find and click create tab or left button
                self.log(vm_name, "Tìm Create tab hoặc nút trái")
                for i in range(MAX_RETRY_FIND_TAB):
                    creation_tab = d.xpath(CONTENT_DESC_CREATE_NEW).exists
                    action_left = d(resourceId=RESOURCE_ID_LEFT_ACTION).exists

                    if creation_tab:
                        self.log(vm_name, "Nhấn Create tab")
                        if not self.safe_click(d, CONTENT_DESC_CREATE_NEW, sleep_after=WAIT_LONG,
                                              vm_name=vm_name, description="Create new button"):
                            self.log(vm_name, "❌ Không click được Create tab", "ERROR")
                            return False
                        break

                    elif action_left:
                        self.log(vm_name, "Nhấn nút trái")
                        if not self.safe_click(d, XPATH_ACTION_LEFT_CONTAINER, sleep_after=WAIT_LONG,
                                              vm_name=vm_name, description="Action left container"):
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
                if not self.safe_click(d, CONTENT_DESC_CREATE_POST, sleep_after=WAIT_LONG,
                                      vm_name=vm_name, description="Create post button"):
                    self.log(vm_name, "⚠️ Không tìm thấy nút Post", "WARNING")
                    self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút Post - Menu có thể đã thay đổi")
                    return False

            self.log(vm_name, "Nhấn post")
            self.safe_click(d, XPATH_POST, sleep_after=WAIT_SHORT,
                                  vm_name=vm_name, description="Post selector button")
                # self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút Post")
                # return False

            # Kiểm tra có file trong gallery hay chưa
            self.log(vm_name, "🔍 Kiểm tra file trong gallery...")
            # ✅ v1.5.32: Tăng timeout từ WAIT_SHORT lên WAIT_LONG (15s) để đợi Instagram refresh gallery
            if not self.wait_for_element(d, XPATH_FIRST_BOX, vm_name=vm_name, description="first box", timeout=WAIT_LONG):
                # File chưa xuất hiện trong gallery → Retry broadcast MediaStore
                self.log(vm_name, "⚠️ File chưa xuất hiện trong gallery")
                if video_filename:
                    self.log(vm_name, "🔄 Đang retry broadcast MediaStore...")
                    self._retry_mediastore_broadcast(adb_address, video_filename, vm_name, max_retries=3)

                    # Kiểm tra lại sau khi retry
                    if not self.wait_for_element(d, XPATH_FIRST_BOX, vm_name=vm_name, description="first box", timeout=WAIT_MEDIUM):
                        # ✅ v1.5.32: Lần cuối cùng thử force refresh gallery (back + reopen)
                        self.log(vm_name, "⚠️ Vẫn không thấy file - Thử force refresh gallery...")

                        # Back ra khỏi gallery picker
                        d.press("back")
                        time.sleep(2)

                        # Vào lại Post gallery
                        self.log(vm_name, "🔄 Mở lại gallery picker...")
                        self.safe_click(d, XPATH_POST, sleep_after=WAIT_SHORT, vm_name=vm_name, description="Post selector (retry)")
                        time.sleep(2)

                        # Check lần cuối
                        if not self.wait_for_element(d, XPATH_FIRST_BOX, vm_name=vm_name, description="first box (after refresh)", timeout=WAIT_LONG):
                            self.log(vm_name, "❌ File vẫn không xuất hiện sau khi force refresh gallery")
                            self._capture_failure_screenshot(adb_address, vm_name, "File không xuất hiện trong gallery sau force refresh")
                            return False
                        else:
                            self.log(vm_name, "✅ File đã xuất hiện sau khi force refresh gallery!")
                    else:
                        self.log(vm_name, "✅ File đã xuất hiện sau khi retry broadcast")
                else:
                    self.log(vm_name, "❌ Không có video_filename để retry broadcast")
                    self._capture_failure_screenshot(adb_address, vm_name, "File không xuất hiện và không có filename để retry")
                    return False
            else:
                self.log(vm_name, "✅ File đã có trong gallery")


            time.sleep(3)
            # Click Next (top)
            self.log(vm_name, "Nhấn Next (trên)")
            if not self.safe_click(d, XPATH_NEXT_BUTTON, sleep_after=WAIT_LONG,
                                  vm_name=vm_name, description="Next button (top)"):
                self.log(vm_name, "⚠️ Không tìm thấy nút Next trên", "WARNING")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút next trên")
                return False

            # Click Next (bottom)
            self.log(vm_name, "Nhấn Next (dưới)")
            if not self.safe_click(d, XPATH_RIGHT_ACTION, sleep_after=WAIT_LONG,
                                  vm_name=vm_name, description="Next button (bottom)"):
                self.log(vm_name, "⚠️ Không tìm thấy nút Next dưới", "WARNING")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút next dưới")
                return False

            # Click Continue if exists
            self.log(vm_name, "Nhấn Continue (nếu có)")
            self.safe_click(d, XPATH_DOWNLOAD_NUX, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT,
                          description="Continue button")

            # Click OK if exists
            self.log(vm_name, "Nhấn OK (nếu có)")
            self.safe_click(d, XPATH_PRIMARY_ACTION, sleep_after=WAIT_LONG,
                          vm_name=vm_name, optional=True, timeout=TIMEOUT_SHORT,
                          description="OK button")

            # Enter caption
            self.log(vm_name, f"📝 Nhập caption: {title}")
            if not self.safe_send_text(d, XPATH_CAPTION_INPUT, title,
                                      sleep_after=WAIT_LONG, vm_name=vm_name,
                                      description="caption input"):
                self.log(vm_name, "❌ Không thể nhập caption", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy caption input - UI có thể đã thay đổi")
                return False

            # Click OK button
            self.log(vm_name, "🔑 Nhấn OK")
            if not self.safe_click(d, XPATH_ACTION_BAR_TEXT, sleep_after=WAIT_LONG,
                                  vm_name=vm_name, description="OK button"):
                self.log(vm_name, "❌ Không tìm thấy nút OK", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút OK sau nhập caption")
                return False

            # Click Share
            self.log(vm_name, "🔑 Nhấn Share")
            if self.wait_for_element(d, XPATH_SHARE_BUTTON, vm_name=vm_name, description="nút share", timeout=WAIT_MEDIUM):
                if d.xpath(XPATH_SHARE_BUTTON).info["enabled"] is True:
                    if not self.safe_click(d, XPATH_SHARE_BUTTON, sleep_after=WAIT_SHORT,
                                        vm_name=vm_name, timeout=2, description="Share button"):
                        self.log(vm_name, "❌ Nút share đã enable nhưng không ấn được", "ERROR")
                        self._capture_failure_screenshot(adb_address, vm_name, "Nút share đã enable nhưng không ấn được - UI upload có thể đã thay đổi")
                        return False
                else:
                    self.log(vm_name,"❌ Nút share không enable","ERROR")
                    self._capture_failure_screenshot(adb_address, vm_name, "Nút share không enable")
                    return False
            else:
                self.log(vm_name, "❌ Không tìm thấy nút share", "ERROR")
                self._capture_failure_screenshot(adb_address, vm_name, "Không tìm thấy nút share")
                return False

            # Click allow 
            self.log(vm_name, "🔑 Nhấn allow")
            self.safe_click(d, XPATH_ALLOW_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)
            # Click Share 2
            self.log(vm_name, "🔑 Nhấn Share 2")
            if self.safe_click(d, XPATH_SHARE_BUTTON_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2):
                # Click Share 3
                self.log(vm_name, "🔑 Nhấn Share 3")
                self.safe_click(d, XPATH_SHARE_BUTTON_2, sleep_after=1,
                            vm_name=vm_name, optional=True, timeout=2)
            # Click allow 
            self.log(vm_name, "🔑 Nhấn allow")
            self.safe_click(d, XPATH_ALLOW_2, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)
                          
            # Click SHARE TO
            self.log(vm_name, "🔑 Nhấn ashare to")
            self.safe_click(d, XPATH_SHARE_TO, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)

            #click not share
            self.log(vm_name, "🔑 Nhấn no share")
            self.safe_click(d, XPATH_NOT_SHARE, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=2)
                          
            # Click "No thanks" if exists
            # self.log(vm_name, "🔑 Nhấn No thanks (nếu có)")
            # self.safe_click(d, XPATH_CANCEL_BUTTON_ID, sleep_after=1,
            #               vm_name=vm_name, optional=True, timeout=3)

            # Wait for post notification
            self.log(vm_name, "⏳ Chờ đăng bài...")
            for i in range(MAX_RETRY_POST_NOTIFICATION):
                if (not d.xpath(XPATH_progress_bar).exists and i > 15):
                    self.log(vm_name, "✅ Đã mất thanh tiến trình!")
                    break
                
                if d.xpath(XPATH_PENDING_MEDIA).exists:
                    self.log(vm_name, "✅ Đã có thông báo đăng bài!")
                    break
                
                if d.xpath(XPATH_RETRY_MEDIA).exists:
                    self.log(vm_name, "❌ Đăng không thành công - Instagram từ chối post")
                    self._capture_failure_screenshot(adb_address, vm_name, "Instagram từ chối đăng bài - Có thể video vi phạm guidelines hoặc UI thay đổi")
                    return False

                if d.xpath(XPATH_CANCEL_BUTTON_ID).exists:
                    self.safe_click(d, XPATH_CANCEL_BUTTON_ID, sleep_after=1,
                          vm_name=vm_name, optional=True, timeout=3)

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
