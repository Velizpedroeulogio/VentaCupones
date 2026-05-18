from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0004_evnc_car_campos_venta")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "EVNC_CAR"
    DROP COLUMN IF EXISTS "EVNC_LOCA",
    ADD COLUMN IF NOT EXISTS "EVNC_NOM" VARCHAR(100);
""",
            reverse_sql="""
ALTER TABLE "EVNC_CAR"
    ADD COLUMN IF NOT EXISTS "EVNC_LOCA" VARCHAR(100),
    DROP COLUMN IF EXISTS "EVNC_NOM";
""",
        ),
    ]
