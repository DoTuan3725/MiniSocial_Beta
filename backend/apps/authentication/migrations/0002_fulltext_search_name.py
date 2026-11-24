"""
Tạo FULLTEXT INDEX dùng ngram parser cho cột users.search_name (chỉ trên MySQL).
ngram (mặc định token 2 ký tự) giúp tìm được cả tên ngắn như "an", "ly" mà FULLTEXT thường bỏ qua.
"""
from django.db import migrations


def create_index(apps, schema_editor):
    if schema_editor.connection.vendor == "mysql":
        schema_editor.execute("CREATE FULLTEXT INDEX ft_users_search_name ON users (search_name) WITH PARSER ngram")


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor == "mysql":
        schema_editor.execute("DROP INDEX ft_users_search_name ON users")


class Migration(migrations.Migration):
    atomic = False  # MySQL không rollback được DDL -> không bọc trong transaction
    dependencies = [("authentication", "0001_initial")]
    operations = [migrations.RunPython(create_index, drop_index)]
