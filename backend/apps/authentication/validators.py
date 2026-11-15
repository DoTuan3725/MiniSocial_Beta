import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """Mật khẩu mạnh: >= 8 ký tự, có chữ hoa, chữ số và ký tự đặc biệt (Báo cáo 2.1.1)."""

    def validate(self, password, user=None):
        errors = []
        if not re.search(r"[A-Z]", password or ""):
            errors.append("Mật khẩu phải có ít nhất 1 chữ in hoa.")
        if not re.search(r"\d", password or ""):
            errors.append("Mật khẩu phải có ít nhất 1 chữ số.")
        if not re.search(r"[^A-Za-z0-9]", password or ""):
            errors.append("Mật khẩu phải có ít nhất 1 ký tự đặc biệt.")
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "Tối thiểu 8 ký tự, gồm chữ in hoa, chữ số và ký tự đặc biệt."
