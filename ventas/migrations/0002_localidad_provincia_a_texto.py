from django.db import migrations


class Migration(migrations.Migration):
    """
    Esta migracion ya fue aplicada anteriormente con contenido diferente.
    El resultado en la DB es:
      - per_localidad_id: VARCHAR(100) — guarda texto libre de localidad
      - per_provincia_id: VARCHAR(100) — guarda texto libre de provincia
      - Las FK constraints originales fueron eliminadas en ese proceso.
    VentaCupones usa estas columnas como texto. El proyecto GBL debera
    ser revisado por separado para adaptar sus referencias a estas columnas.
    """

    dependencies = [("ventas", "0001_tablas_mov_y_evnc_ven")]

    operations = []
