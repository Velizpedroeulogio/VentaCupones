from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0019_msg_proc_msgid")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "EVN_DEF"
    ADD COLUMN IF NOT EXISTS "EVN_FCHDES" DATE,
    ADD COLUMN IF NOT EXISTS "EVN_FCHHAS" DATE,
    ADD COLUMN IF NOT EXISTS "EVN_ESTADO" CHAR(1) DEFAULT 'H';
""",
            reverse_sql="""
ALTER TABLE "EVN_DEF"
    DROP COLUMN IF EXISTS "EVN_FCHDES",
    DROP COLUMN IF EXISTS "EVN_FCHHAS",
    DROP COLUMN IF EXISTS "EVN_ESTADO";
""",
        ),
    ]
