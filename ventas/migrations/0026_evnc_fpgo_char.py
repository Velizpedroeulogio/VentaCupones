from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0025_drop_pvt_mevn_ment")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "EVNC_CAR"
    ALTER COLUMN "EVNC_FPGO" TYPE CHAR(1)
    USING LEFT("EVNC_FPGO"::TEXT, 1);
""",
            reverse_sql="""
ALTER TABLE "EVNC_CAR"
    ALTER COLUMN "EVNC_FPGO" TYPE NUMERIC
    USING NULL;
""",
        ),
    ]
