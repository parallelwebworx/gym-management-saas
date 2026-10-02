"""
Enable pg_trgm and add GIN trigram indexes on members.full_name / phone for fuzzy
search. Postgres-only: a no-op on other backends so SQLite dev/test still migrates.
"""
from django.db import migrations

TABLE = "members_member"


def create_trgm(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    schema_editor.execute(
        f"CREATE INDEX IF NOT EXISTS members_member_name_trgm "
        f"ON {TABLE} USING gin (full_name gin_trgm_ops)"
    )
    schema_editor.execute(
        f"CREATE INDEX IF NOT EXISTS members_member_phone_trgm "
        f"ON {TABLE} USING gin (phone gin_trgm_ops)"
    )


def drop_trgm(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP INDEX IF EXISTS members_member_name_trgm")
    schema_editor.execute("DROP INDEX IF EXISTS members_member_phone_trgm")


class Migration(migrations.Migration):
    dependencies = [("members", "0001_initial")]
    operations = [migrations.RunPython(create_trgm, drop_trgm)]
