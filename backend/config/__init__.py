# PyMySQL đóng vai trò driver MySQL thuần Python (chạy tốt trên cả amd64 và arm64).
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover
    pass

from .celery import app as celery_app  # noqa: E402

__all__ = ("celery_app",)
