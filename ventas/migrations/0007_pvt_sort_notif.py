from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0006_fpgo_nid")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "PVT_SORT"
    ADD COLUMN IF NOT EXISTS "PVT_BURL" VARCHAR(200),
    ADD COLUMN IF NOT EXISTS "PVT_WMSG" VARCHAR(500),
    ADD COLUMN IF NOT EXISTS "PVT_EMSJ" VARCHAR(200);

UPDATE "PVT_SORT"
   SET "PVT_BURL" = 'https://visor-gbl-production.up.railway.app',
       "PVT_WMSG" = 'Hola {nombre}! Tu cupón N° {cupon} del Bingo San Martín está confirmado. Podés verlo en: {url}',
       "PVT_EMSJ" = 'Tu cupón Bingo San Martín - N° {cupon}'
 WHERE "PVT_FCHX" = 20260401;
""",
            reverse_sql="""
ALTER TABLE "PVT_SORT"
    DROP COLUMN IF EXISTS "PVT_BURL",
    DROP COLUMN IF EXISTS "PVT_WMSG",
    DROP COLUMN IF EXISTS "PVT_EMSJ";
""",
        ),
    ]
