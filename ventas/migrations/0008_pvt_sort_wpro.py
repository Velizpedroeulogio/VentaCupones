from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0007_pvt_sort_notif")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "PVT_SORT"
    ADD COLUMN IF NOT EXISTS "PVT_WPRO" CHAR(1);

UPDATE "PVT_SORT"
   SET "PVT_WPRO" = 'C'
 WHERE "PVT_FCHX" = 20260401;
""",
            reverse_sql="""
ALTER TABLE "PVT_SORT"
    DROP COLUMN IF EXISTS "PVT_WPRO";
""",
        ),
    ]
