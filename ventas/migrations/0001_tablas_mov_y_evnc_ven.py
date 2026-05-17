from django.db import migrations


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="""
CREATE TABLE IF NOT EXISTS "PRD_MOV" (
    "ID"       SERIAL PRIMARY KEY,
    "PRD_DSCR" VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS "CDM_MOV" (
    "ID"       SERIAL PRIMARY KEY,
    "CDM_DSCR" VARCHAR(100) NOT NULL,
    "CDM_ACCI" CHAR(1)      NOT NULL
);

CREATE TABLE IF NOT EXISTS "MDP_MOV" (
    "ID"       SERIAL PRIMARY KEY,
    "MDP_FCHA" DATE           NOT NULL,
    "MDP_HORA" TIME           NOT NULL,
    "PRD_ID"   INTEGER        NOT NULL,
    "EVN_NUM"  INTEGER        NOT NULL,
    "VEN_COD"  VARCHAR(30)    NOT NULL,
    "CDM_ID"   INTEGER        NOT NULL,
    "MDP_VALO" NUMERIC(15,2)  NOT NULL,
    "MDP_ACCI" CHAR(1)        NOT NULL,
    "MDP_ESTD" CHAR(1)        NOT NULL,
    "MDP_CPTE" VARCHAR(50),
    "MDP_REFE" VARCHAR(100)
);

ALTER TABLE "EVNC_CAR"
    ALTER COLUMN "EVNC_VEN" TYPE VARCHAR(30) USING "EVNC_VEN"::text;
""",
            reverse_sql="""
DROP TABLE IF EXISTS "MDP_MOV";
DROP TABLE IF EXISTS "CDM_MOV";
DROP TABLE IF EXISTS "PRD_MOV";
""",
        ),
    ]
