from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0013_departamento_localidad")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "EVN_DEF"
    ADD COLUMN IF NOT EXISTS "EVN_PCJCOM" NUMERIC(5,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS "EVN_TOPVTA" INTEGER       DEFAULT 0;

ALTER TABLE "USR_VTAS"
    ADD COLUMN IF NOT EXISTS "USR_PCJCOM" NUMERIC(5,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS "USR_TOPVTA" INTEGER       DEFAULT 0,
    ADD COLUMN IF NOT EXISTS "USR_NRND"   INTEGER       DEFAULT 0;
""",
            reverse_sql="""
ALTER TABLE "EVN_DEF"
    DROP COLUMN IF EXISTS "EVN_PCJCOM",
    DROP COLUMN IF EXISTS "EVN_TOPVTA";

ALTER TABLE "USR_VTAS"
    DROP COLUMN IF EXISTS "USR_PCJCOM",
    DROP COLUMN IF EXISTS "USR_TOPVTA",
    DROP COLUMN IF EXISTS "USR_NRND";
""",
        ),
    ]
