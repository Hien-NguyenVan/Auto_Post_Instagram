"""
Text Utilities
Các hàm tiện ích xử lý text, string manipulation
"""


def remove_keywords_from_text(text, keywords_string):
    """
    Loại bỏ các từ khóa khỏi text (case-sensitive)

    Args:
        text: Chuỗi text cần xử lý
        keywords_string: Chuỗi từ khóa phân tách bằng dấu phẩy (vd: "#tiktok, #Tiktok, _R")

    Returns:
        str: Text đã loại bỏ từ khóa

    Example:
        >>> remove_keywords_from_text("Video #tiktok hay #Tiktok nhất", "#tiktok, #Tiktok")
        "Video  hay  nhất"
    """
    if not text or not keywords_string:
        return text

    # Parse keywords: split by comma, strip whitespace
    keywords = [kw.strip() for kw in keywords_string.split(",") if kw.strip()]

    if not keywords:
        return text

    result = text

    # Remove each keyword (case-sensitive)
    for keyword in keywords:
        result = result.replace(keyword, "")

    # Clean up multiple spaces
    while "  " in result:
        result = result.replace("  ", " ")

    return result.strip()


def parse_keywords_input(keywords_string):
    """
    Parse chuỗi từ khóa nhập vào thành list

    Args:
        keywords_string: Chuỗi từ khóa phân tách bằng dấu phẩy

    Returns:
        list: Danh sách từ khóa đã clean

    Example:
        >>> parse_keywords_input("#tiktok, #Tiktok, _R, ")
        ["#tiktok", "#Tiktok", "_R"]
    """
    if not keywords_string:
        return []

    keywords = [kw.strip() for kw in keywords_string.split(",") if kw.strip()]
    return keywords


def preview_keyword_removal(text, keywords_string):
    """
    Preview kết quả sau khi loại bỏ từ khóa (dùng cho UI preview)

    Args:
        text: Text gốc
        keywords_string: Chuỗi từ khóa

    Returns:
        tuple: (text_sau_khi_xoa, so_luong_thay_doi)
    """
    result = remove_keywords_from_text(text, keywords_string)
    changed = 1 if result != text else 0
    return result, changed
