from django.db import migrations


class Migration(migrations.Migration):
    """
    Revierte los cambios de 0002 sobre app_gbl_persona:
    - Vuelve per_localidad_id y per_provincia_id a INTEGER
    - Recrea las FK constraints originales hacia app_core_localidad y app_core_provincia
    """

    dependencies = [("ventas", "0002_localidad_provincia_a_texto")]

    operations = [
        migrations.RunSQL(
            sql="""
-- Limpiar cualquier valor no numerico que se haya podido grabar
UPDATE "app_gbl_persona"
   SET "per_localidad_id" = NULL
 WHERE "per_localidad_id" IS NOT NULL
   AND "per_localidad_id" !~ '^[0-9]+$';

UPDATE "app_gbl_persona"
   SET "per_provincia_id" = NULL
 WHERE "per_provincia_id" IS NOT NULL
   AND "per_provincia_id" !~ '^[0-9]+$';

-- Volver a INTEGER
ALTER TABLE "app_gbl_persona"
    ALTER COLUMN "per_localidad_id" TYPE INTEGER USING "per_localidad_id"::integer,
    ALTER COLUMN "per_provincia_id" TYPE INTEGER USING "per_provincia_id"::integer;

-- Recrear FK constraints con los nombres originales de Django
ALTER TABLE "app_gbl_persona"
    ADD CONSTRAINT "app_gbl_persona_per_localidad_id_882cdacd_fk_app_core_localidad_id"
        FOREIGN KEY ("per_localidad_id")
        REFERENCES "app_core_localidad" ("id")
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "app_gbl_persona"
    ADD CONSTRAINT "app_gbl_persona_per_provincia_id_8531ed34_fk_app_core_provincia_id"
        FOREIGN KEY ("per_provincia_id")
        REFERENCES "app_core_provincia" ("id")
        DEFERRABLE INITIALLY DEFERRED;
""",
            reverse_sql="-- no reversible",
        ),
    ]
