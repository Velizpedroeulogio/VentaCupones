from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0015_usr_tusr")]

    operations = [
        migrations.RunSQL(
            sql="""
ALTER TABLE "MDP_MOV"
    ADD COLUMN IF NOT EXISTS "MDP_IREF" NUMERIC(15,2);

UPDATE "PRD_MOV" SET "PRD_DSCR" = 'Rendiciones' WHERE "ID" = 2;

INSERT INTO "PRD_MOV" ("ID", "PRD_DSCR")
VALUES (3, 'Comisiones')
ON CONFLICT ("ID") DO NOTHING;
""",
            reverse_sql="""
ALTER TABLE "MDP_MOV"
    DROP COLUMN IF EXISTS "MDP_IREF";

UPDATE "PRD_MOV" SET "PRD_DSCR" = 'Comisiones' WHERE "ID" = 2;

DELETE FROM "PRD_MOV" WHERE "ID" = 3;
""",
        ),
    ]
