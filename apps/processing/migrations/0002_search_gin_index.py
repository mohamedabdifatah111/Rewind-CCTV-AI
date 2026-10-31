from django.db import migrations

# Matches the expression Django generates for SearchVector("search_text", config="english"), so Postgres can use the index.
SQL = ("CREATE INDEX IF NOT EXISTS framedesc_fts_gin ON processing_framedescription "
       "USING gin (to_tsvector('english'::regconfig, COALESCE(search_text, '')))")

def forwards(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(SQL)

def backwards(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP INDEX IF EXISTS framedesc_fts_gin")

class Migration(migrations.Migration):
    dependencies = [("processing", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
