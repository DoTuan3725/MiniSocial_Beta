import html
import unicodedata

import bleach
from unidecode import unidecode


def sanitize_text(value, max_length=None):
    """
    Lọc XSS bằng Bleach: loại bỏ toàn bộ thẻ HTML, chỉ giữ văn bản thuần.
    Sau đó unescape để lưu đúng ký tự gốc (React sẽ tự escape khi hiển thị).
    """
    if value is None:
        return ""
    cleaned = bleach.clean(str(value), tags=[], attributes={}, strip=True, strip_comments=True)
    cleaned = html.unescape(cleaned)
    cleaned = unicodedata.normalize("NFC", cleaned).strip()
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def unaccent(value):
    """'Nguyễn Văn Đức' -> 'nguyen van duc' (phục vụ tìm kiếm tiếng Việt không dấu)."""
    return unidecode(value or "").lower().strip()
