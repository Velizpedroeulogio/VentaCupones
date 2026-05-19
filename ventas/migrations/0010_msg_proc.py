from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0009_pvt_sort_wpro_mail")]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE TABLE IF NOT EXISTS "MSG_PROC" (
    "MSG_ID"   SERIAL PRIMARY KEY,
    "MSG_FCHA" DATE,
    "MSG_HORA" TIME,
    "MSG_IDPR" VARCHAR(30),
    "MSG_EVN"  INTEGER,
    "MSG_SEC"  INTEGER,
    "MSG_REFE" VARCHAR(200),
    "MSG_TXTO" VARCHAR(500),
    "MSG_MRKA" CHAR(1),
    "MSG_FCHR" DATE,
    "MSG_HORR" TIME,
    "MSG_ERRO" VARCHAR(500)
);
""",
            reverse_sql='DROP TABLE IF EXISTS "MSG_PROC";',
        ),
    ]
