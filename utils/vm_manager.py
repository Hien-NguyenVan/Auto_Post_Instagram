"""
VM Resource Manager - Quản lý truy cập đồng thời vào máy ảo.

Đảm bảo chỉ có 1 luồng sử dụng 1 máy ảo tại 1 thời điểm.
Các luồng khác phải chờ cho đến khi máy ảo được giải phóng.
"""
import threading
import logging
import time
import subprocess
from typing import Optional


class VMManager:
    """
    Singleton manager để quản lý locks cho từng máy ảo.

    Sử dụng threading.Lock để đảm bảo chỉ 1 luồng truy cập 1 VM tại 1 thời điểm.
    """

    _instance = None
    _creation_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._creation_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._vm_locks = {}  # {vm_name: threading.Lock()}
            self._locks_lock = threading.Lock()  # Lock để tạo lock mới an toàn
            self.logger = logging.getLogger(__name__)
            self._initialized = True

    def acquire_vm(self, vm_name: str, timeout: float = 5400, caller: str = "") -> bool:
        """
        Khóa máy ảo để sử dụng độc quyền.

        Nếu VM đang được sử dụng bởi luồng khác, sẽ CHỜ cho đến khi:
        - VM được giải phóng, HOẶC
        - Hết timeout

        Args:
            vm_name: Tên máy ảo cần khóa
            timeout: Thời gian chờ tối đa (giây). Mặc định 5400s = 1.5 giờ
            caller: Tên người gọi (để log)

        Returns:
            bool: True nếu khóa thành công, False nếu timeout
        """
        # Tạo lock cho VM nếu chưa có (thread-safe)
        with self._locks_lock:
            if vm_name not in self._vm_locks:
                self._vm_locks[vm_name] = threading.Lock()
                self.logger.info(f"Created new lock for VM: {vm_name}")

        vm_lock = self._vm_locks[vm_name]
        caller_info = f"[{caller}] " if caller else ""

        # Thử khóa VM
        self.logger.info(f"{caller_info}Attempting to acquire VM '{vm_name}' (timeout={timeout}s)...")

        acquired = vm_lock.acquire(blocking=True, timeout=timeout)

        if acquired:
            self.logger.info(f"{caller_info}✅ Successfully acquired VM '{vm_name}'")
            return True
        else:
            self.logger.warning(f"{caller_info}⏱️ Timeout waiting for VM '{vm_name}' after {timeout}s")
            return False

    def release_vm(self, vm_name: str, caller: str = ""):
        """
        Giải phóng máy ảo sau khi sử dụng xong.

        Args:
            vm_name: Tên máy ảo cần giải phóng
            caller: Tên người gọi (để log)
        """
        if vm_name not in self._vm_locks:
            self.logger.warning(f"Attempted to release non-existent lock for VM: {vm_name}")
            return

        caller_info = f"[{caller}] " if caller else ""

        try:
            self._vm_locks[vm_name].release()
            self.logger.info(f"{caller_info}🔓 Released VM '{vm_name}'")
        except RuntimeError as e:
            # Lock chưa được acquire hoặc đã release rồi
            self.logger.error(f"{caller_info}Error releasing VM '{vm_name}': {e}")

    def is_locked(self, vm_name: str) -> bool:
        """
        Kiểm tra xem VM có đang bị khóa không (non-blocking check).

        Args:
            vm_name: Tên máy ảo

        Returns:
            bool: True nếu VM đang bị khóa
        """
        if vm_name not in self._vm_locks:
            return False

        # Thử acquire với timeout=0 (non-blocking)
        vm_lock = self._vm_locks[vm_name]
        if vm_lock.acquire(blocking=False):
            # Nếu acquire được thì VM đang rảnh, nhớ release lại
            vm_lock.release()
            return False
        else:
            # Không acquire được = VM đang bị khóa
            return True

    def get_status(self) -> dict:
        """
        Lấy trạng thái của tất cả VM locks.

        Returns:
            dict: {vm_name: locked (bool)}
        """
        status = {}
        with self._locks_lock:
            for vm_name in self._vm_locks:
                status[vm_name] = self.is_locked(vm_name)
        return status

    @staticmethod
    def wait_vm_ready(vm_name: str, ldconsole_path: str, timeout: int = 60,
                      check_interval: int = 2, log_callback=None) -> bool:
        """
        Chờ máy ảo khởi động hoàn toàn (status = "1" trong ldconsole list2).

        Args:
            vm_name: Tên máy ảo
            ldconsole_path: Đường dẫn đến ldconsole.exe
            timeout: Thời gian chờ tối đa (giây)
            check_interval: Thời gian chờ giữa các lần check (giây)
            log_callback: Optional callback function(msg) để log ra UI

        Returns:
            bool: True nếu VM đã ready, False nếu timeout
        """
        logger = logging.getLogger(__name__)
        elapsed = 0
        last_status = None
        last_progress_log = 0

        logger.info(f"⏳ Chờ máy ảo '{vm_name}' khởi động (timeout={timeout}s)...")

        while elapsed < timeout:
            try:
                result = subprocess.run(
                    [ldconsole_path, "list2"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )

                # Parse output để check status
                for line in result.stdout.splitlines():
                    parts = line.split(",")
                    # Format: index,name,title,top_window,running,pid
                    if len(parts) >= 5 and parts[1].strip() == vm_name:
                        status = parts[4].strip()

                        # Log khi status thay đổi
                        if status != last_status:
                            status_name = {"0": "Tắt", "1": "Đang chạy", "2": "Đang khởi động"}.get(status, status)
                            if log_callback:
                                log_callback(f"   📊 VM status: {status_name} (sau {elapsed}s)")
                            logger.info(f"VM '{vm_name}' status changed: {status} ({status_name})")
                            last_status = status

                        if status == "1":
                            if log_callback:
                                log_callback(f"✅ Máy ảo đã sẵn sàng (sau {elapsed}s)")
                            logger.info(f"✅ Máy ảo '{vm_name}' đã sẵn sàng sau {elapsed}s")
                            return True
                        break

            except subprocess.TimeoutExpired:
                msg = f"⚠️ ldconsole list2 timeout (vẫn đang chờ...)"
                if log_callback:
                    log_callback(msg)
                logger.warning(f"ldconsole list2 timeout khi check VM '{vm_name}'")
            except Exception as e:
                msg = f"⚠️ Lỗi check VM: {e}"
                if log_callback:
                    log_callback(msg)
                logger.error(f"Lỗi khi check status VM '{vm_name}': {e}")

            # Log progress mỗi 15s để user biết vẫn đang chờ
            if elapsed > 0 and elapsed - last_progress_log >= 15:
                if log_callback:
                    status_str = f"status={last_status}" if last_status else "checking..."
                    log_callback(f"   ⏳ Vẫn đang chờ... ({elapsed}s/{timeout}s, {status_str})")
                last_progress_log = elapsed

            time.sleep(check_interval)
            elapsed += check_interval

        msg = f"❌ Timeout {timeout}s - VM không ready (status cuối: {last_status})"
        if log_callback:
            log_callback(msg)
        logger.error(f"⏱️ Timeout {timeout}s - Máy ảo '{vm_name}' chưa sẵn sàng (status: {last_status})")
        return False

    @staticmethod
    def wait_adb_ready(device: str, adb_path: str, timeout: int = 30,
                       check_interval: int = 2, log_callback=None) -> bool:
        """
        Chờ ADB kết nối đến device.

        Args:
            device: Device name (vd: "emulator-5556")
            adb_path: Đường dẫn đến adb.exe
            timeout: Thời gian chờ tối đa (giây)
            check_interval: Thời gian chờ giữa các lần check (giây)
            log_callback: Optional callback function(msg) để log ra UI

        Returns:
            bool: True nếu ADB đã connect, False nếu timeout
        """
        logger = logging.getLogger(__name__)
        elapsed = 0
        last_progress_log = 0

        logger.info(f"⏳ Chờ ADB kết nối đến '{device}' (timeout={timeout}s)...")

        while elapsed < timeout:
            try:
                result = subprocess.run(
                    [adb_path, "devices"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )

                # Check if device is in the output
                if device in result.stdout:
                    if log_callback:
                        log_callback(f"✅ ADB đã kết nối (sau {elapsed}s)")
                    logger.info(f"✅ ADB đã kết nối đến '{device}' sau {elapsed}s")
                    return True
                else:
                    logger.debug(f"Device '{device}' chưa xuất hiện trong 'adb devices'")

            except subprocess.TimeoutExpired:
                msg = f"⚠️ 'adb devices' timeout (vẫn đang chờ...)"
                if log_callback and elapsed > 10:  # Chỉ log sau 10s
                    log_callback(msg)
                logger.warning(f"adb devices timeout khi check '{device}'")
            except Exception as e:
                msg = f"⚠️ Lỗi check ADB: {e}"
                if log_callback:
                    log_callback(msg)
                logger.error(f"Lỗi khi check ADB '{device}': {e}")

            # Log progress mỗi 10s
            if elapsed > 0 and elapsed - last_progress_log >= 10:
                if log_callback:
                    log_callback(f"   ⏳ Vẫn đang chờ ADB... ({elapsed}s/{timeout}s)")
                last_progress_log = elapsed

            time.sleep(check_interval)
            elapsed += check_interval

        msg = f"❌ Timeout {timeout}s - ADB không kết nối được"
        if log_callback:
            log_callback(msg)
        logger.error(f"⏱️ Timeout {timeout}s - ADB chưa kết nối đến '{device}'")
        return False

    @staticmethod
    def wait_vm_stopped(vm_name: str, ldconsole_path: str, timeout: int = 60,
                        check_interval: int = 2) -> bool:
        """
        Chờ máy ảo TẮT hoàn toàn (status = "0" trong ldconsole list2).

        QUAN TRỌNG: Phải gọi hàm này sau khi quit VM để đảm bảo VM đã tắt hẳn
        trước khi release lock. Tránh race condition khi luồng khác acquire lock
        trong lúc VM chưa tắt xong.

        Args:
            vm_name: Tên máy ảo
            ldconsole_path: Đường dẫn đến ldconsole.exe
            timeout: Thời gian chờ tối đa (giây)
            check_interval: Thời gian chờ giữa các lần check (giây)

        Returns:
            bool: True nếu VM đã tắt hoàn toàn, False nếu timeout
        """
        logger = logging.getLogger(__name__)
        elapsed = 0

        logger.info(f"⏳ Chờ máy ảo '{vm_name}' tắt hoàn toàn (timeout={timeout}s)...")

        while elapsed < timeout:
            try:
                result = subprocess.run(
                    [ldconsole_path, "list2"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )

                # Parse output để check status
                vm_found = False
                for line in result.stdout.splitlines():
                    parts = line.split(",")
                    # Format: index,name,title,top_window,running,pid
                    if len(parts) >= 5 and parts[1].strip() == vm_name:
                        vm_found = True
                        is_stopped = parts[4].strip() == "0"

                        if is_stopped:
                            logger.info(f"✅ Máy ảo '{vm_name}' đã tắt hoàn toàn sau {elapsed}s")
                            return True
                        else:
                            logger.debug(f"VM '{vm_name}' status: {parts[4]} (đang tắt...)")
                        break

                # Nếu không tìm thấy VM trong list -> coi như đã xóa/tắt
                if not vm_found:
                    logger.info(f"✅ Máy ảo '{vm_name}' không còn trong danh sách (đã tắt)")
                    return True

            except subprocess.TimeoutExpired:
                logger.warning(f"ldconsole list2 timeout khi check VM '{vm_name}'")
            except Exception as e:
                logger.error(f"Lỗi khi check status VM '{vm_name}': {e}")

            time.sleep(check_interval)
            elapsed += check_interval

        logger.error(f"⏱️ Timeout {timeout}s - Máy ảo '{vm_name}' chưa tắt hoàn toàn")
        return False


# Singleton instance
vm_manager = VMManager()
