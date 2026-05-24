from django.core.management.base import BaseCommand
from django.db import connection
from ventas.services import calcular_hmac_cupon


class Command(BaseCommand):
    help = 'Recalcula INF_ADIC (HMAC) para todos los registros de INF_URL'

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            cur.execute('SELECT "INF_EVN", "INF_SEC" FROM "INF_URL" ORDER BY "INF_EVN", "INF_SEC"')
            rows = cur.fetchall()

        total = len(rows)
        self.stdout.write(f'Registros encontrados: {total}')

        if total == 0:
            self.stdout.write('Nada que procesar.')
            return

        actualizados = 0
        sin_clave    = 0

        with connection.cursor() as cur:
            for evn, sec in rows:
                codigo = calcular_hmac_cupon(evn, sec)
                if not codigo:
                    sin_clave += 1
                    continue
                cur.execute(
                    'UPDATE "INF_URL" SET "INF_ADIC"=%s WHERE "INF_EVN"=%s AND "INF_SEC"=%s',
                    (codigo, evn, sec)
                )
                actualizados += 1

        if sin_clave:
            self.stdout.write(self.style.WARNING(
                f'CUPON_HMAC_KEY no configurada — {sin_clave} registros sin actualizar.'
            ))
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {actualizados} de {total} registros actualizados.'
        ))
