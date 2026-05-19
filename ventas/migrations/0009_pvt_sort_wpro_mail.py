from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0008_pvt_sort_wpro")]

    operations = [
        migrations.RunSQL(
            sql="""
UPDATE "PVT_SORT"
   SET "PVT_WPRO" = 'M'
 WHERE "PVT_FCHX" = 20260401;
""",
            reverse_sql="""
UPDATE "PVT_SORT"
   SET "PVT_WPRO" = 'C'
 WHERE "PVT_FCHX" = 20260401;
""",
        ),
    ]
