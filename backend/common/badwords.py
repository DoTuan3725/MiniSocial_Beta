"""
Bộ lọc từ ngữ thô tục tiếng Việt bằng Regex (dùng chung, phục vụ phân hệ Admin & Kiểm duyệt).
Phân hệ Post gọi trước khi lưu bài/bình luận; kết quả kích hoạt sự kiện tạo báo cáo tự động.
"""

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

WORDLIST = Path(__file__).parent / "data" / "badwords_vi.txt"


@lru_cache(maxsize=1)
def _pattern():
    words = []
    for line in WORDLIST.read_text(encoding="utf-8").splitlines():
        line = unicodedata.normalize("NFC", line.strip().lower())
        if line and not line.startswith("#"):
            words.append(re.escape(line).replace(r"\ ", r"\s+"))
    if not words:
        return None
    words.sort(key=len, reverse=True)
    return re.compile(r"(?<!\w)(" + "|".join(words) + r")(?!\w)", re.IGNORECASE | re.UNICODE)


def _normalize(text):
    return unicodedata.normalize("NFC", text or "")


def find_badwords(text):
    pattern = _pattern()
    if not pattern:
        return []
    return sorted({m.group(0).lower() for m in pattern.finditer(_normalize(text))})


def contains_badwords(text):
    return bool(find_badwords(text))


def censor(text):
    pattern = _pattern()
    if not pattern:
        return text
    return pattern.sub(lambda m: "*" * len(m.group(0)), _normalize(text))
