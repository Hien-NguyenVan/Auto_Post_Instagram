"""
Base class for Instagram automation.

This module contains shared functionality for Instagram login and posting automation,
including logging, safe UI element interaction, and error handling.
"""
import time
import logging
from typing import Optional, Callable
import uiautomator2 as u2

from constants import TIMEOUT_DEFAULT, WAIT_SHORT


class BaseInstagramAutomation:
    """
    Base class for Instagram automation tasks.

    Provides shared methods for:
    - Logging (console + callback + file)
    - Safe UI element clicking
    - Safe text input
    - Error handling
    """

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize base Instagram automation.

        Args:
            log_callback: Optional callback function that receives (vm_name, message)
                         for custom logging (e.g., to UI)
        """
        self.log_callback = log_callback
        self.logger = logging.getLogger(self.__class__.__name__)

    def log(self, vm_name: str, message: str, level: str = "INFO"):
        """
        Unified logging method.

        Logs to:
        1. Python logging system (file + console)
        2. User callback (if provided)

        Args:
            vm_name: Name of the virtual machine
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Format message with VM name
        formatted_msg = f"[{vm_name}] {message}"

        # Log to standard logger
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, formatted_msg)

        # Call user callback if provided (for UI updates)
        if self.log_callback:
            try:
                self.log_callback(vm_name, message)
            except Exception as e:
                self.logger.error(f"Error in log callback: {e}")

    def safe_click(
        self,
        d: u2.Device,
        xpath: str,
        timeout: int = TIMEOUT_DEFAULT,
        vm_name: str = "",
        sleep_after: Optional[float] = None,
        optional: bool = False
    ) -> bool:
        """
        Click an element safely with timeout and error handling.

        Args:
            d: UIAutomator2 device object
            xpath: XPath of the element to click
            timeout: Maximum wait time in seconds
            vm_name: VM name for logging
            sleep_after: Time to wait after clicking (optional)
            optional: If True, don't treat missing element as error

        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            el = d.xpath(xpath)

            if el.wait(timeout=timeout):
                el.click()
                self.log(vm_name, f"✅ Click thành công: {xpath[:50]}...")

                if sleep_after:
                    self.log(vm_name, f"⏱️ Chờ {sleep_after}s sau khi click...")
                    time.sleep(sleep_after)

                return True
            else:
                if optional:
                    # Optional element not found - not an error
                    self.log(vm_name, f"⚠️ Không thấy (optional) {xpath[:50]}... → bỏ qua", "WARNING")
                    return True

                # Required element not found - error
                self.log(
                    vm_name,
                    f"❌ Hết thời gian {timeout}s mà không tìm thấy: {xpath[:50]}...",
                    "ERROR"
                )
                return False

        except Exception as e:
            self.log(vm_name, f"⚠️ Lỗi khi click {xpath[:50]}...: {e}", "ERROR")
            self.logger.exception(f"Exception in safe_click for {xpath}")
            return False

    def safe_send_text(
        self,
        d: u2.Device,
        xpath: str,
        text: str,
        timeout: int = TIMEOUT_DEFAULT,
        sleep_after: float = WAIT_SHORT,
        vm_name: str = ""
    ) -> bool:
        """
        Send text to an input field safely with timeout and error handling.

        Args:
            d: UIAutomator2 device object
            xpath: XPath of the input element
            text: Text to send
            timeout: Maximum wait time in seconds
            sleep_after: Time to wait after sending text
            vm_name: VM name for logging

        Returns:
            bool: True if text was sent successfully
        """
        try:
            if d.xpath(xpath).wait(timeout=timeout):
                d.xpath(xpath).set_text(text)
                self.log(vm_name, f"📝 Đã nhập text vào: {xpath[:50]}...")
                time.sleep(sleep_after)
                return True
            else:
                self.log(
                    vm_name,
                    f"❌ Không tìm thấy input field: {xpath[:50]}...",
                    "ERROR"
                )
                return False

        except Exception as e:
            self.log(vm_name, f"⚠️ Không tìm thấy hoặc nhập lỗi {xpath[:50]}...: {e}", "ERROR")
            self.logger.exception(f"Exception in safe_send_text for {xpath}")
            return False

    def wait_for_element(
        self,
        d: u2.Device,
        xpath: str,
        timeout: int = TIMEOUT_DEFAULT,
        vm_name: str = "",
        description: str = ""
    ) -> bool:
        """
        Wait for an element to appear.

        Args:
            d: UIAutomator2 device object
            xpath: XPath of the element
            timeout: Maximum wait time in seconds
            vm_name: VM name for logging
            description: Human-readable description of what we're waiting for

        Returns:
            bool: True if element appeared, False if timeout
        """
        desc = description or f"element {xpath[:50]}..."
        self.log(vm_name, f"⏳ Chờ {desc}...")

        try:
            if d.xpath(xpath).wait(timeout=timeout):
                self.log(vm_name, f"✅ {desc} đã xuất hiện")
                return True
            else:
                self.log(vm_name, f"❌ {desc} không xuất hiện trong {timeout}s", "WARNING")
                return False
        except Exception as e:
            self.log(vm_name, f"⚠️ Lỗi khi chờ {desc}: {e}", "ERROR")
            self.logger.exception(f"Exception in wait_for_element for {xpath}")
            return False

    def element_exists(self, d: u2.Device, xpath: str) -> bool:
        """
        Check if element exists without waiting.

        Args:
            d: UIAutomator2 device object
            xpath: XPath of the element

        Returns:
            bool: True if element exists
        """
        try:
            return d.xpath(xpath).exists
        except Exception:
            return False
