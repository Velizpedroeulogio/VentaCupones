from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0016_mdp_iref_prd3")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "EVN_DEF"
    ADD COLUMN IF NOT EXISTS "EVN_MSGQR" VARCHAR(300) DEFAULT '';
""",
            reverse_sql="""
ALTER TABLE "EVN_DEF"
    DROP COLUMN IF EXISTS "EVN_MSGQR";
""",
        ),
    ]
