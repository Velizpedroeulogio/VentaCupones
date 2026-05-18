from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0005_evnc_car_nom_loca")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "MDP_MOV"
    ADD COLUMN IF NOT EXISTS "MDP_FPGO" CHAR(1),
    ADD COLUMN IF NOT EXISTS "MDP_NID"  INTEGER;

ALTER TABLE "EVNC_CAR"
    ADD COLUMN IF NOT EXISTS "EVNC_FPGO" CHAR(1);
""",
            reverse_sql="""
ALTER TABLE "MDP_MOV"
    DROP COLUMN IF EXISTS "MDP_FPGO",
    DROP COLUMN IF EXISTS "MDP_NID";

ALTER TABLE "EVNC_CAR"
    DROP COLUMN IF EXISTS "EVNC_FPGO";
""",
        ),
    ]
