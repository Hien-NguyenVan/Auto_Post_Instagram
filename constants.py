"""
Constants for the Instagram automation tool.

This file contains all magic numbers, timeout values, and XPath selectors
to make the code more maintainable and easier to modify.
"""

# ==================== TIMING CONSTANTS ====================
# Sleep durations (in seconds)
WAIT_SHORT = 2
WAIT_MEDIUM = 5
WAIT_LONG = 10
WAIT_EXTRA_LONG = 15

# Timeout values (in seconds)
TIMEOUT_DEFAULT = 15
TIMEOUT_MINUTE = 60
TIMEOUT_SHORT = 5
TIMEOUT_MEDIUM = 10
TIMEOUT_EXTENDED = 30
TIMEOUT_APP_OPEN = 60

# Retry limits
MAX_RETRY_OPEN_APP = 15
MAX_RETRY_POST_NOTIFICATION = 2700
MAX_RETRY_VM_STATUS = 30
MAX_RETRY_FIND_TAB = 10

# Intervals
VM_STATUS_CHECK_INTERVAL = 2  # seconds between VM status checks
DOWNLOAD_CHECK_INTERVAL = 2   # seconds between download progress checks
POST_CHECK_INTERVAL = 2       # seconds between post status checks

# ==================== XPATH SELECTORS ====================
# Common elements
XPATH_INSTAGRAM_APP = '//*[@text="Instagram"]'

# Login flow
XPATH_ALREADY_HAVE_ACCOUNT = '//*[@text="I already have an account"]'
XPATH_USERNAME_INPUT = '//*[@text="Username, email or mobile number"]'
XPATH_PASSWORD_INPUT = '//*[@text="Password"]'
XPATH_LOGIN_BUTTON = '//*[@text="Log in"]'
XPATH_TRY_ANOTHER_WAY = '//*[@text="Try another way"]'
XPATH_AUTH_APP = '//*[@text="Authentication app"]'
XPATH_CONTINUE_BUTTON = '//*[@text="Continue"]'
XPATH_CODE_INPUT = '//*[@text="Code"]'
XPATH_SAVE_BUTTON = '//*[@text="Save"]'
XPATH_SKIP_BUTTON = '//*[@text="Skip"]'
XPATH_DENY_BUTTON = '//*[@text="DENY"]'
XPATH_CANCEL_BUTTON = '//*[@text="Cancel"]'

# Instagram UI elements (resource IDs)
RESOURCE_ID_FEED_TAB = "com.instagram.android:id/feed_tab"
RESOURCE_ID_PROFILE_TAB = "com.instagram.android:id/profile_tab"
RESOURCE_ID_PROFILE_NAME = "com.instagram.android:id/profile_header_full_name_above_vanity"
RESOURCE_ID_PROMO_BUTTON = "com.instagram.android:id/igds_promo_dialog_action_button"
RESOURCE_ID_LEFT_ACTION = "com.instagram.android:id/left_action_bar_buttons"
RESOURCE_ID_ACTION_LEFT_CONTAINER = "com.instagram.android:id/action_bar_buttons_container_left"
RESOURCE_ID_NEXT_BUTTON = "com.instagram.android:id/next_button_textview"
RESOURCE_ID_RIGHT_ACTION = "com.instagram.android:id/clips_right_action_button"
RESOURCE_ID_DOWNLOAD_NUX = "com.instagram.android:id/clips_download_privacy_nux_button"
RESOURCE_ID_PRIMARY_ACTION = "com.instagram.android:id/bb_primary_action_container"
RESOURCE_ID_CAPTION_INPUT = "com.instagram.android:id/caption_input_text_view"
RESOURCE_ID_ACTION_BAR_TEXT = "com.instagram.android:id/action_bar_button_text"
RESOURCE_ID_SHARE_BUTTON = "com.instagram.android:id/share_button"
RESOURCE_ID_SHARE_BUTTON_2 = "com.instagram.android:id/igds_alert_dialog_primary_button"
RESOURCE_ID_CANCEL_BUTTON = "com.instagram.android:id/appirater_cancel_button"
RESOURCE_ID_PENDING_MEDIA = "com.instagram.android:id/row_pending_media_reshare_button"
RETRY_ID_MEDIA = "com.instagram.android:id/row_pending_media_retry_button"
# XPath for resource IDs (formatted)
XPATH_FEED_TAB = f'//*[@resource-id="{RESOURCE_ID_FEED_TAB}"]'
XPATH_PROFILE_TAB = f'//*[@resource-id="{RESOURCE_ID_PROFILE_TAB}"]'
XPATH_PROFILE_NAME = f'//*[@resource-id="{RESOURCE_ID_PROFILE_NAME}"]'
XPATH_PROMO_BUTTON = f'//*[@resource-id="{RESOURCE_ID_PROMO_BUTTON}"]'
XPATH_NEXT_BUTTON = f'//*[@resource-id="{RESOURCE_ID_NEXT_BUTTON}"]'
XPATH_RIGHT_ACTION = f'//*[@resource-id="{RESOURCE_ID_RIGHT_ACTION}"]'
XPATH_DOWNLOAD_NUX = f'//*[@resource-id="{RESOURCE_ID_DOWNLOAD_NUX}"]'
XPATH_PRIMARY_ACTION = f'//*[@resource-id="{RESOURCE_ID_PRIMARY_ACTION}"]'
XPATH_CAPTION_INPUT = f'//*[@resource-id="{RESOURCE_ID_CAPTION_INPUT}"]'
XPATH_ACTION_BAR_TEXT = f'//*[@resource-id="{RESOURCE_ID_ACTION_BAR_TEXT}"]'
XPATH_SHARE_BUTTON = f'//*[@resource-id="{RESOURCE_ID_SHARE_BUTTON}"]'
XPATH_SHARE_BUTTON_2 = f'//*[@resource-id="{RESOURCE_ID_SHARE_BUTTON_2}"]'
XPATH_CANCEL_BUTTON_ID = f'//*[@resource-id="{RESOURCE_ID_CANCEL_BUTTON}"]'
XPATH_PENDING_MEDIA = f'//*[@resource-id="{RESOURCE_ID_PENDING_MEDIA}"]'
XPATH_LEFT_ACTION = f'//*[@resource-id="{RESOURCE_ID_LEFT_ACTION}"]'
XPATH_ACTION_LEFT_CONTAINER = f'//*[@resource-id="{RESOURCE_ID_ACTION_LEFT_CONTAINER}"]'
XPATH_RETRY_MEDIA=f'//*[@resource-id="{RETRY_ID_MEDIA}"]'

# Content descriptions
CONTENT_DESC_CREATE_NEW = '//*[@content-desc="Create New"]'
CONTENT_DESC_CREATE_POST = '//*[@content-desc="Create new post"]'

# ==================== API CONSTANTS ====================
# 2FA API endpoint
TWOFA_API_URL = "https://2fa.live/tok/{key}"

# ==================== FILE SYSTEM CONSTANTS ====================
# Video processing
VIDEO_TEMP_DIR = "temp"
VIDEO_DOWNLOAD_DIR = "downloads"
DCIM_PATH = "/sdcard/DCIM"  # Android DCIM path

# ==================== CHROME/BROWSER ====================
CHROME_PACKAGE = "com.android.chrome"
CHROME_TITLE_ID = "com.android.chrome:id/title"

# ==================== INSTAGRAM PACKAGE ====================
INSTAGRAM_PACKAGE = "com.instagram.android"

# ==================== VM CONFIGURATION ====================
DEFAULT_VM_RESOLUTION = "720,1280,320"
DEFAULT_VM_CPU = "2"
DEFAULT_VM_MEMORY = "2048"
ADB_DEBUG_SETTING = '"basicSettings.adbDebug": 1,'
