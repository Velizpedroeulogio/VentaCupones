from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0018_msg_proc")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "MSG_PROC"
    ADD COLUMN IF NOT EXISTS "MSG_ID" BIGSERIAL;
""",
            reverse_sql="""
ALTER TABLE "MSG_PROC"
    DROP COLUMN IF EXISTS "MSG_ID";
""",
        ),
    ]
