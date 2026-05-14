import psycopg2

PG_DSN = "postgresql://postgres:ASUxkRzTtTGBQNkVbPNTLxCOlFWKxaeO@shuttle.proxy.rlwy.net:12906/railway"

def encriptar_pwd(pwd):
    def comp_dig(c): return str(9 - int(c)) if c.isdigit() else c
    mapa = {**{chr(i): chr(ord("Z")-(i-ord("A"))) for i in range(ord("A"), ord("Z")+1)},
            **{chr(i): chr(ord("z")-(i-ord("a"))) for i in range(ord("a"), ord("z")+1)}}
    def comp_char(c): return mapa.get(c, c)
    return "".join(comp_dig(c) if c.isdigit() else comp_char(c) for c in str(pwd))

cnx = psycopg2.connect(PG_DSN)
cur = cnx.cursor()

# --- Crear tablas ---
cur.execute("""
CREATE TABLE IF NOT EXISTS "USR_VTAS" (
    "USR_EVNX" INTEGER      NOT NULL,
    "USR_IDEU" VARCHAR(20)  NOT NULL,
    "USR_NOMB" VARCHAR(100),
    "USR_PWDX" VARCHAR(100),
    "USR_ESTD" CHAR(1)      DEFAULT 'A',
    "USR_FCHI" INTEGER,
    "USR_FCHB" INTEGER,
    "USR_FCHD" INTEGER,
    "USR_FCHH" INTEGER,
    "USR_REFE" VARCHAR(100),
    "USR_FCHC" INTEGER,
    PRIMARY KEY ("USR_EVNX", "USR_IDEU")
)
""")
print("Tabla USR_VTAS: OK")

cur.execute("""
CREATE TABLE IF NOT EXISTS "PVT_SORT" (
    "PVT_EVN"  INTEGER        NOT NULL,
    "PVT_FCHX" INTEGER        NOT NULL,
    "PVT_FCHD" INTEGER,
    "PVT_FCHH" INTEGER,
    "PVT_CHN1" NUMERIC(10,2),
    "PVT_CHN2" NUMERIC(10,2),
    "PVT_CHN3" NUMERIC(10,2),
    "PVT_CHN4" NUMERIC(10,2),
    "PVT_CHN5" NUMERIC(10,2),
    "PVT_CHN6" NUMERIC(10,2),
    "PVT_CHN7" NUMERIC(10,2),
    "PVT_CHN8" NUMERIC(10,2),
    "PVT_CHN9" NUMERIC(10,2),
    PRIMARY KEY ("PVT_EVN", "PVT_FCHX")
)
""")
print("Tabla PVT_SORT: OK")

# --- Insertar usuario de prueba ---
pwd_enc = encriptar_pwd("abg127")
print(f"Password encriptada: {pwd_enc}")

cur.execute("""
INSERT INTO "USR_VTAS"
    ("USR_EVNX","USR_IDEU","USR_NOMB","USR_PWDX","USR_ESTD",
     "USR_FCHI","USR_FCHD","USR_FCHH","USR_REFE")
VALUES (%s,%s,%s,%s,'A',%s,%s,%s,%s)
ON CONFLICT ("USR_EVNX","USR_IDEU") DO UPDATE
    SET "USR_NOMB"=%s, "USR_PWDX"=%s, "USR_ESTD"='A',
        "USR_FCHD"=%s, "USR_FCHH"=%s
""", (
    2115, "pVeliz", "Pedro Veliz", pwd_enc,
    20260101, 20260101, 20261231, "velizpedroeulogio@gmail.com",
    "Pedro Veliz", pwd_enc, 20260101, 20261231
))
print(f"Usuario pVeliz evento 2115: {'insertado/actualizado'}")

# --- Insertar PVT_SORT ---
cur.execute("""
INSERT INTO "PVT_SORT"
    ("PVT_EVN","PVT_FCHX","PVT_FCHD","PVT_FCHH",
     "PVT_CHN3","PVT_CHN6","PVT_CHN9")
VALUES (%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT ("PVT_EVN","PVT_FCHX") DO UPDATE
    SET "PVT_FCHD"=%s,"PVT_FCHH"=%s,
        "PVT_CHN3"=%s,"PVT_CHN6"=%s,"PVT_CHN9"=%s
""", (
    2115, 20260401, 20260401, 20260430,
    15000, 25000, 35000,
    20260401, 20260430,
    15000, 25000, 35000
))
print("PVT_SORT evento 2115 fecha 20260401: insertado/actualizado")

cnx.commit()

# --- Verificar ---
cur.execute('SELECT "USR_IDEU","USR_NOMB","USR_ESTD","USR_FCHD","USR_FCHH" FROM "USR_VTAS" WHERE "USR_EVNX"=2115')
print("\nUSR_VTAS evento 2115:")
for r in cur.fetchall():
    print(f"  {r}")

cur.execute('SELECT "PVT_FCHX","PVT_FCHD","PVT_FCHH","PVT_CHN3","PVT_CHN6","PVT_CHN9" FROM "PVT_SORT" WHERE "PVT_EVN"=2115')
print("\nPVT_SORT evento 2115:")
for r in cur.fetchall():
    print(f"  {r}")

cnx.close()
print("\nSetup completado.")
