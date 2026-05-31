from django.db import migrations


class Migration(migrations.Migration):
    """
    Carga los nombres para la plantilla Meta WA del evento 2115.
    Ajustar PVT_MEVN y PVT_MENT si cambia el evento o la entidad.
    """

    dependencies = [("ventas", "0023_pvt_sort_meta_nombres")]

    operations = [
        migrations.RunSQL(
            sql="""
UPDATE "PVT_SORT"
   SET "PVT_MEVN" = '1er. Bingo Digital de CASM',
       "PVT_MENT" = 'Club San Martin de Tucumán'
 WHERE "PVT_EVN" = 2115;
""",
            reverse_sql="""
UPDATE "PVT_SORT"
   SET "PVT_MEVN" = NULL,
       "PVT_MENT" = NULL
 WHERE "PVT_EVN" = 2115;
""",
        ),
    ]
