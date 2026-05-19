from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0010_msg_proc")]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE TABLE IF NOT EXISTS "INF_URL" (
    "INF_EVN" INTEGER NOT NULL,
    "INF_SEC" INTEGER NOT NULL,
    "INF_DV1" INTEGER,
    "INF_DV2" INTEGER,
    "INF_DTA" TEXT,
    PRIMARY KEY ("INF_EVN", "INF_SEC")
);
""",
            reverse_sql='DROP TABLE IF EXISTS "INF_URL";',
        ),
    ]
