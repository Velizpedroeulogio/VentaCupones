from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0020_evn_qr_estado")]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "INF_URL" ADD COLUMN IF NOT EXISTS "INF_ADIC" VARCHAR(20);',
            reverse_sql='ALTER TABLE "INF_URL" DROP COLUMN IF EXISTS "INF_ADIC";',
        ),
    ]
