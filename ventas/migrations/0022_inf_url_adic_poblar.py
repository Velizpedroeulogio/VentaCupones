import hashlib
import hmac as _hmac_mod
import os
from django.db import migrations


def poblar_hmac(apps, schema_editor):
    clave = os.environ.get("CUPON_HMAC_KEY", "")
    if not clave:
        return
    with schema_editor.connection.cursor() as cur:
        cur.execute('SELECT "INF_EVN", "INF_SEC" FROM "INF_URL"')
        rows = cur.fetchall()
    updates = []
    for evn, sec in rows:
        msg = f"{int(evn):05d}{int(sec):06d}".encode()
        codigo = _hmac_mod.new(clave.encode(), msg, hashlib.sha256).hexdigest()[:8]
        updates.append((codigo, evn, sec))
    if updates:
        with schema_editor.connection.cursor() as cur:
            cur.executemany(
                'UPDATE "INF_URL" SET "INF_ADIC"=%s WHERE "INF_EVN"=%s AND "INF_SEC"=%s',
                updates
            )


class Migration(migrations.Migration):

    dependencies = [("ventas", "0021_inf_url_adic")]

    operations = [
        migrations.RunPython(poblar_hmac, migrations.RunPython.noop),
    ]
