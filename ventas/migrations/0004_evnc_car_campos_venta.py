from django.db import migrations


class Migration(migrations.Migration):
    """
    Agrega a EVNC_CAR los campos de datos del comprador y
    crea EVNC_LOCA para texto libre de localidad (uso futuro).
    """

    dependencies = [("ventas", "0003_revertir_localidad_provincia")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "EVNC_CAR"
    ADD COLUMN IF NOT EXISTS "EVNC_NID"  INTEGER,
    ADD COLUMN IF NOT EXISTS "EVNC_DOM"  VARCHAR(200),
    ADD COLUMN IF NOT EXISTS "EVNC_LOC"  VARCHAR(200),
    ADD COLUMN IF NOT EXISTS "EVNC_REF"  VARCHAR(200),
    ADD COLUMN IF NOT EXISTS "EVNC_LOCA" VARCHAR(100);
""",
            reverse_sql="""
ALTER TABLE "EVNC_CAR"
    DROP COLUMN IF EXISTS "EVNC_NID",
    DROP COLUMN IF EXISTS "EVNC_DOM",
    DROP COLUMN IF EXISTS "EVNC_LOC",
    DROP COLUMN IF EXISTS "EVNC_REF",
    DROP COLUMN IF EXISTS "EVNC_LOCA";
""",
        ),
    ]
