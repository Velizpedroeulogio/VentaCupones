from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0014_rendicion_campos")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "USR_VTAS"
    ADD COLUMN IF NOT EXISTS "USR_TUSR" CHAR(1) NOT NULL DEFAULT 'V';
""",
            reverse_sql="""
ALTER TABLE "USR_VTAS"
    DROP COLUMN IF EXISTS "USR_TUSR";
""",
        ),
    ]
