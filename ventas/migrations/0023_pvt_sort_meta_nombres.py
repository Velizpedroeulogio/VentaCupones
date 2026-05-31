from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0022_inf_url_adic_poblar")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "PVT_SORT"
    ADD COLUMN IF NOT EXISTS "PVT_MEVN" VARCHAR(200),
    ADD COLUMN IF NOT EXISTS "PVT_MENT" VARCHAR(200);
""",
            reverse_sql="""
ALTER TABLE "PVT_SORT"
    DROP COLUMN IF EXISTS "PVT_MEVN",
    DROP COLUMN IF EXISTS "PVT_MENT";
""",
        ),
    ]
