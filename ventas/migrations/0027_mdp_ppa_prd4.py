from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ventas", "0026_evnc_fpgo_char")]

    operations = [
        # 1. Agregar PRD_ID=4 'Pagos Parciales' en PRD_MOV
        migrations.RunSQL(
            sql="""
INSERT INTO "PRD_MOV" ("ID", "PRD_DSCR")
VALUES (4, 'Pagos Parciales')
ON CONFLICT ("ID") DO NOTHING;
""",
            reverse_sql="""
DELETE FROM "PRD_MOV" WHERE "ID" = 4;
""",
        ),

        # 2. Crear tabla MDP_PPA (Pagos Parciales en Movimientos de Producto)
        migrations.RunSQL(
            sql="""
CREATE TABLE "MDP_PPA" (
    "PPA_ID"   SERIAL        PRIMARY KEY,
    "EVN_NUM"  INTEGER       NOT NULL,
    "EVNC_SEC" INTEGER       NOT NULL,
    "VEN_COD"  VARCHAR(20)   NOT NULL,
    "MDP_NID"  CHAR(11)      NOT NULL,
    "PPA_FCHA" DECIMAL(8,0)  NOT NULL,
    "PPA_IMPO" DECIMAL(15,2) NOT NULL,
    "PPA_SLDO" DECIMAL(15,2) NOT NULL,
    "PPA_FCMP" DECIMAL(8,0)  NOT NULL,
    "PPA_ESTD" CHAR(1)       NOT NULL DEFAULT 'P'
);
""",
            reverse_sql="""
DROP TABLE IF EXISTS "MDP_PPA";
""",
        ),
    ]
