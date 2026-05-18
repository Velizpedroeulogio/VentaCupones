import os
from datetime import datetime
from django.db import connection

_KEY1 = os.environ.get("GBYL_KEY1", "dvtcksqonz")
_KEY2 = os.environ.get("GBYL_KEY2", "ABCDEFGHIJ")


# ------------------------------------------------------------------ DB HELPERS
def _fetchone(sql, params=()):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _fetchall(sql, params=()):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


# ------------------------------------------------------------ ENCRIPTACION BYL
def complemento_digito(c):
    return str(9 - int(c)) if str(c).isdigit() else c


def complemento_char(c):
    mapa = {**{chr(i): chr(ord("Z") - (i - ord("A"))) for i in range(ord("A"), ord("Z") + 1)},
            **{chr(i): chr(ord("z") - (i - ord("a"))) for i in range(ord("a"), ord("z") + 1)}}
    return mapa.get(c, c)


def transformar_texto(txt):
    return "".join(
        complemento_digito(c) if c.isdigit() else complemento_char(c)
        for c in str(txt or "")
    )


def encriptar_pwd(pwd):
    return transformar_texto(str(pwd or "").strip())


# ------------------------------------------------------------------ FECHA
def fecha_hoy_aaaammdd():
    return int(datetime.now().strftime("%Y%m%d"))


def fmt_fecha(fecha):
    s = str(fecha).strip()
    if len(s) != 8 or not s.isdigit():
        return s
    return f"{s[6:8]}.{s[4:6]}.{s[0:4]}"


# ------------------------------------------------------------------ EVENTO
def get_evento(evn):
    row = _fetchone(
        'SELECT "EVN_DSC" FROM "EVN_DEF" WHERE "EVN_NUM" = %s',
        (evn,)
    )
    return str(row[0] or "") if row else ""


# ------------------------------------------------------------------ IMAGEN
def get_imagen_evento(evn, static_url="/static/"):
    import os
    base = f"{static_url}ventas/img"
    img_dir = os.path.join("static", "ventas", "img")
    for cand in [f"Evn{evn}_02a.jpeg",
                 f"Evn{evn}_01.jpeg"]:
        if os.path.exists(os.path.join(img_dir, cand)):
            return f"{base}/{cand}"
    return ""


def get_imagen_sponsor(evn, static_url="/static/"):
    import os
    base = f"{static_url}ventas/img"
    img_dir = os.path.join("static", "ventas", "img")
    cand = f"Evn{evn}_02b.jpeg"
    if os.path.exists(os.path.join(img_dir, cand)):
        return f"{base}/{cand}"
    return ""


# ------------------------------------------------------------------ USUARIOS
def validate_user(evn, usuario, pwd):
    """
    Valida usuario/contraseña contra USR_VTAS.
    Devuelve (ok, nombre, mensaje_error).
    """
    row = _fetchone(
        'SELECT "USR_NOMB","USR_PWDX","USR_ESTD","USR_FCHD","USR_FCHH"'
        ' FROM "USR_VTAS"'
        ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
        (evn, str(usuario or "").strip())
    )
    if not row:
        return False, "", "Usuario no encontrado"

    nombre, pwd_enc, estd, fchd, fchh = row

    if estd != "A":
        return False, "", "Usuario no habilitado"

    hoy = fecha_hoy_aaaammdd()
    if fchd and hoy < int(fchd):
        return False, "", "Usuario aún no habilitado"
    if fchh and hoy > int(fchh):
        return False, "", "Habilitación vencida"

    if encriptar_pwd(pwd) != str(pwd_enc or ""):
        return False, "", "Contraseña incorrecta"

    return True, str(nombre or ""), ""


def get_user_refe(evn, usuario):
    row = _fetchone(
        'SELECT "USR_REFE" FROM "USR_VTAS"'
        ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
        (evn, str(usuario or "").strip())
    )
    return str(row[0] or "") if row else ""


def cambiar_pwd(evn, usuario, pwd_nueva):
    hoy = fecha_hoy_aaaammdd()
    with connection.cursor() as cur:
        cur.execute(
            'UPDATE "USR_VTAS" SET "USR_PWDX" = %s, "USR_FCHC" = %s'
            ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
            (encriptar_pwd(pwd_nueva), hoy, evn, str(usuario or "").strip())
        )
        return cur.rowcount > 0


# ------------------------------------------------------------------ PVT_SORT
def get_pvt_sort(evn):
    hoy = fecha_hoy_aaaammdd()
    row = _fetchone(
        'SELECT "PVT_FCHX","PVT_FCHD","PVT_FCHH",'
        '       "PVT_CHN1","PVT_CHN2","PVT_CHN3","PVT_CHN4","PVT_CHN5",'
        '       "PVT_CHN6","PVT_CHN7","PVT_CHN8","PVT_CHN9"'
        ' FROM "PVT_SORT"'
        ' WHERE "PVT_EVN" = %s AND "PVT_FCHX" <= %s'
        ' ORDER BY "PVT_FCHX" DESC'
        ' LIMIT 1',
        (evn, hoy)
    )
    if not row:
        return None
    precios = {}
    for i, val in enumerate(row[3:], start=1):
        if val is not None:
            try:
                precios[i] = float(val)
            except Exception:
                pass
    rangos = {}
    try:
        rrow = _fetchone(
            'SELECT "PVT_SCD1","PVT_SCH1","PVT_SCD2","PVT_SCH2",'
            '       "PVT_SCD3","PVT_SCH3","PVT_SCD4","PVT_SCH4",'
            '       "PVT_SCD5","PVT_SCH5","PVT_SCD6","PVT_SCH6",'
            '       "PVT_SCD7","PVT_SCH7","PVT_SCD8","PVT_SCH8",'
            '       "PVT_SCD9","PVT_SCH9"'
            ' FROM "PVT_SORT"'
            ' WHERE "PVT_EVN" = %s AND "PVT_FCHX" <= %s'
            ' ORDER BY "PVT_FCHX" DESC LIMIT 1',
            (evn, hoy)
        )
        if rrow:
            for i in range(1, 10):
                scd, sch = rrow[(i - 1) * 2], rrow[(i - 1) * 2 + 1]
                if scd is not None and sch is not None:
                    try:
                        rangos[i] = {"scd": int(scd), "sch": int(sch)}
                    except Exception:
                        pass
    except Exception:
        pass
    return {
        "pvt_fchx": row[0],
        "pvt_fchd": row[1],
        "pvt_fchh": row[2],
        "precios":  precios,
        "rangos":   rangos,
    }


# ------------------------------------------------------------------ FECHAS SORTEO
def get_fechas_sorteo(evn, fchd, fchh):
    rows = _fetchall(
        'SELECT "Srt_Fcha" FROM "SrtFechas"'
        ' WHERE "Evn_Num" = %s AND "Srt_Fcha" BETWEEN %s AND %s'
        ' ORDER BY "Srt_Fcha"',
        (evn, int(fchd), int(fchh))
    )
    return [{"raw": str(r[0]), "fmt": fmt_fecha(r[0])} for r in rows if r[0]]


def get_sorteos_de_fecha(evn, fecha):
    rows = _fetchall(
        'SELECT A."Srt_Nro", A."Srt_Dscr", B."SRT_PRE1", B."SRT_PRE2"'
        '  FROM "SrtFchNum" A'
        '  LEFT JOIN "SORTEOS" B'
        '    ON B."EVN_NUM" = A."Evn_Num" AND B."SRT_NUM" = A."Srt_Nro"'
        ' WHERE A."Evn_Num" = %s AND A."Srt_Fcha" = %s'
        ' ORDER BY A."Srt_Nro"',
        (evn, int(fecha))
    )
    return [
        {"nro": str(r[0] or ""), "dscr": str(r[1] or ""), "pre1": str(r[2] or ""), "pre2": str(r[3] or "")}
        for r in rows
    ]


# ------------------------------------------------------------------ AYUDA
def get_textos_ayuda(codi):
    try:
        rows = _fetchall(
            'SELECT "HLPD_TEXT" FROM "HLP_TXT"'
            ' WHERE "HLPD_CODI" = %s ORDER BY "HLPD_SECU"',
            (codi,)
        )
        if rows:
            return [str(r[0]) for r in rows if r[0]]
    except Exception:
        pass
    if codi == "SOMOS":
        return [
            "ABG Servicios Informáticos es una empresa especializada en la automatización de procesos informáticos,",
            "con más de 40 años de trayectoria, brindando soluciones a la industria azucarera, al comercio en general",
            "y al sector financiero en particular.",
        ]
    if codi == "HELP1":
        return [
            "Esta aplicación permite la venta de Cupones Digitales de Bingo ABG.",
            "Seleccioná una fecha de sorteo para ver los premios disponibles.",
            "Elegí la cantidad de chances y el sistema te asignará tu cupón.",
        ]
    return ["No hay información disponible."]


# ------------------------------------------------------------------ CUPONES
def get_proximo_cupon(evn):
    row = _fetchone(
        'SELECT "EVNC_SEC" FROM "EVNC_CAR"'
        ' WHERE "EVNC_NUM" = %s AND "EVNC_EST" = %s'
        ' ORDER BY "EVNC_SEC" LIMIT 1',
        (evn, 'P')
    )
    return int(row[0]) if row else None


def get_cartones_cupon(evn, sec):
    rows = _fetchall(
        'SELECT A."EVNC_NUM", A."EVNC_SEC", A."EVNC_SUB",'
        '       B."MTZ_NUM", B."CAR_SER", B."CAR_NUM",'
        '       B."CAR_LIS", A."EVNC_TPO", A."EVNC_EST"'
        '  FROM "EVNC_CAR" A'
        '  LEFT JOIN "MTZ_CAR" B'
        '    ON B."MTZ_NUM" = A."MTZ_NUM" AND B."CAR_SER" = A."CAR_SER"'
        '   AND B."CAR_NUM" = A."CAR_NUM"'
        ' WHERE A."EVNC_NUM" = %s AND A."EVNC_SEC" = %s'
        ' ORDER BY A."EVNC_NUM", A."EVNC_SEC", A."EVNC_SUB"',
        (evn, sec)
    )
    return [
        {
            "sub":  str(r[2] or ""),
            "ser":  str(r[4] or ""),
            "num":  str(r[5] or ""),
            "lis":  _decodificar_lis(str(r[6] or ""), r[5] or 1),
        }
        for r in rows
    ]


def _decodificar_lis(lis, car_num):
    if not lis or lis[0].isdigit():
        return [p for p in lis.split(":") if p.strip()]
    key_first, key_second = (_KEY2, _KEY1) if int(car_num) % 2 == 0 else (_KEY1, _KEY2)
    result = []
    i = 0
    while i + 1 < len(lis):
        c1, c2 = lis[i], lis[i + 1]
        pos1, pos2 = key_first.find(c1), key_second.find(c2)
        if pos1 >= 0 and pos2 >= 0:
            d1 = "0" if pos1 == 9 else str(pos1 + 1)
            d2 = "0" if pos2 == 9 else str(pos2 + 1)
            result.append(d1 + d2)
        i += 3
    return result


# ------------------------------------------------------------------ CODIFICACION
def _codificar_num(num):
    n = int(num)
    tens, units = n // 10, n % 10
    def _idx(d): return 9 if d == 0 else d - 1
    enc_odd  = _KEY1[_idx(tens)] + _KEY2[_idx(units)]
    enc_even = _KEY2[_idx(tens)] + _KEY1[_idx(units)]
    return enc_odd, enc_even


_EST_DISPONIBLE = (
    "(\"EVNC_EST\" = 'P' OR (\"EVNC_EST\" = 'X' AND \"EVNC_TIME\" < NOW() - INTERVAL '5 minutes'))"
)
_EST_DISPONIBLE_A = (
    "(A.\"EVNC_EST\" = 'P' OR (A.\"EVNC_EST\" = 'X' AND A.\"EVNC_TIME\" < NOW() - INTERVAL '5 minutes'))"
)


def get_secuencias_disponibles(evn, scd, sch, nums_pref=None):
    params = [evn, scd, sch]
    if nums_pref:
        like_parts = []
        for num in nums_pref:
            enc_odd, enc_even = _codificar_num(num)
            like_parts.append('(B."CAR_LIS" LIKE %s OR B."CAR_LIS" LIKE %s)')
            params += [f'%{enc_odd}:%', f'%{enc_even}:%']
        sql = (
            'SELECT DISTINCT A."EVNC_SEC"'
            '  FROM "EVNC_CAR" A'
            '  LEFT JOIN "MTZ_CAR" B'
            '    ON B."MTZ_NUM" = A."MTZ_NUM" AND B."CAR_SER" = A."CAR_SER"'
            '   AND B."CAR_NUM" = A."CAR_NUM"'
            ' WHERE A."EVNC_NUM" = %s AND A."EVNC_SEC" BETWEEN %s AND %s'
            '   AND ' + _EST_DISPONIBLE_A +
            '   AND ' + ' AND '.join(like_parts) +
            ' ORDER BY A."EVNC_SEC" LIMIT 5'
        )
    else:
        sql = (
            'SELECT DISTINCT "EVNC_SEC" FROM "EVNC_CAR"'
            ' WHERE "EVNC_NUM" = %s AND "EVNC_SEC" BETWEEN %s AND %s'
            '   AND ' + _EST_DISPONIBLE +
            ' ORDER BY "EVNC_SEC" LIMIT 5'
        )
    rows = _fetchall(sql, params)
    return [int(r[0]) for r in rows]


def reservar_cupon(evn, sec, usuario):
    with connection.cursor() as cur:
        cur.execute(
            'UPDATE "EVNC_CAR" SET "EVNC_EST" = %s, "EVNC_VEN" = %s, "EVNC_TIME" = NOW()'
            ' WHERE "EVNC_NUM" = %s AND "EVNC_SEC" = %s AND "EVNC_EST" = %s',
            ('X', str(usuario or ''), evn, int(sec), 'P')
        )
        return cur.rowcount > 0


def vender_cupon(evn, sec, usuario, nid=None, dom=None, loc=None, ref=None, precio=0):
    from datetime import date, datetime
    hoy  = date.today()
    ahora = datetime.now().time()
    with connection.cursor() as cur:
        cur.execute(
            'UPDATE "EVNC_CAR"'
            ' SET "EVNC_EST"=%s,"EVNC_VEN"=%s,"EVNC_TIME"=NOW(),'
            '     "EVNC_NID"=%s,"EVNC_DOM"=%s,"EVNC_LOC"=%s,"EVNC_REF"=%s'
            ' WHERE "EVNC_NUM"=%s AND "EVNC_SEC"=%s',
            ('V', str(usuario or ''), nid, dom, loc, ref, evn, int(sec))
        )
        if cur.rowcount == 0:
            return False
        cur.execute(
            'INSERT INTO "MDP_MOV"'
            ' ("MDP_FCHA","MDP_HORA","PRD_ID","EVN_NUM","VEN_COD","CDM_ID",'
            '  "MDP_VALO","MDP_ACCI","MDP_ESTD","MDP_CPTE")'
            ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (hoy, ahora, 1, evn, str(usuario or ''), 1,
             precio, 'C', 'I', str(sec).zfill(6))
        )
        return True


# ------------------------------------------------------------------ PUBLICACIONES
def get_publicaciones(evn):
    hoy = fecha_hoy_aaaammdd()
    try:
        rows = _fetchall(
            'SELECT "PUBC_CODI","PUBC_DSCR","PUBC_IMAG","PUBC_ENLC"'
            '  FROM "PUB_DEF"'
            ' WHERE "PUBC_EVN" = %s AND "PUBC_ESTD" = %s'
            '   AND %s BETWEEN "PUBC_VIG1" AND "PUBC_VIG2"'
            ' ORDER BY "PUBC_ORDN","PUBC_CODI"',
            (evn, "A", hoy)
        )
        return [
            {"codi": str(r[0] or ""), "dscr": str(r[1] or ""),
             "imag": str(r[2] or ""), "enlc": str(r[3] or "")}
            for r in rows
        ]
    except Exception:
        return []


# ------------------------------------------------------------------ PERSONA
_PERSONA_KEYS = [
    'id', 'per_numero_identidad', 'per_fecha_nac', 'per_nombre',
    'per_calle', 'per_puerta', 'per_piso', 'per_depto', 'per_barrio',
    'per_codigo_postal', 'per_telefono', 'per_celular', 'per_email',
    'per_localidad_id', 'per_provincia_id', 'per_tipo_identidad_id',
    'per_tipo_persona_id', 'per_alias_cbu', 'per_cbu',
]


def get_persona(numero_identidad):
    row = _fetchone(
        'SELECT id, per_numero_identidad, per_fecha_nac, per_nombre,'
        '  per_calle, per_puerta, per_piso, per_depto, per_barrio,'
        '  per_codigo_postal, per_telefono, per_celular, per_email,'
        '  per_localidad_id, per_provincia_id, per_tipo_identidad_id,'
        '  per_tipo_persona_id, per_alias_cbu, per_cbu'
        ' FROM "app_gbl_persona"'
        ' WHERE "per_numero_identidad" = %s',
        (int(numero_identidad),)
    )
    if not row:
        return None
    return {k: (str(v) if v is not None else '') for k, v in zip(_PERSONA_KEYS, row)}


def save_persona(data):
    provincia_id = get_or_create_provincia(data.get('per_provincia_id'))
    localidad_id = get_or_create_localidad(data.get('per_localidad_id'), provincia_id)

    with connection.cursor() as cur:
        cur.execute(
            'INSERT INTO "app_gbl_persona"'
            ' ("per_numero_identidad","per_fecha_nac","per_nombre",'
            '  "per_calle","per_puerta","per_piso","per_depto","per_barrio",'
            '  "per_codigo_postal","per_telefono","per_celular","per_email",'
            '  "per_localidad_id","per_provincia_id","per_tipo_identidad_id",'
            '  "per_tipo_persona_id","per_alias_cbu","per_cbu")'
            ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (
                int(data['per_numero_identidad']),
                data.get('per_fecha_nac') or None,
                data['per_nombre'],
                data.get('per_calle') or None,
                data.get('per_puerta') or None,
                data.get('per_piso') or None,
                data.get('per_depto') or None,
                data.get('per_barrio') or None,
                data.get('per_codigo_postal') or None,
                data.get('per_telefono') or None,
                data.get('per_celular') or None,
                data.get('per_email') or None,
                localidad_id,
                provincia_id,
                int(data['per_tipo_identidad_id']),
                int(data['per_tipo_persona_id']),
                data.get('per_alias_cbu') or None,
                data.get('per_cbu') or None,
            )
        )
        return cur.rowcount > 0


# ------------------------------------------------------------------ GET OR CREATE LOOKUP

def get_or_create_provincia(nombre):
    nombre = str(nombre or '').strip()
    if not nombre:
        return None
    row = _fetchone(
        'SELECT id FROM "app_core_provincia" WHERE UPPER("pro_provincia") = UPPER(%s)',
        (nombre,)
    )
    if row:
        return row[0]
    with connection.cursor() as cur:
        cur.execute(
            'INSERT INTO "app_core_provincia" ("pro_provincia", "pro_codigo31662") VALUES (%s, %s) RETURNING id',
            (nombre, '')
        )
        return cur.fetchone()[0]


def get_or_create_localidad(nombre, provincia_id):
    nombre = str(nombre or '').strip()
    if not nombre or not provincia_id:
        return None
    row = _fetchone(
        'SELECT id FROM "app_core_localidad"'
        ' WHERE UPPER("loc_nombre") = UPPER(%s) AND "loc_provincia_id" = %s',
        (nombre, provincia_id)
    )
    if row:
        return row[0]
    with connection.cursor() as cur:
        cur.execute(
            'INSERT INTO "app_core_localidad" ("loc_nombre", "loc_cp", "loc_provincia_id") VALUES (%s, %s, %s) RETURNING id',
            (nombre, '', provincia_id)
        )
        return cur.fetchone()[0]


# ------------------------------------------------------------------ LOOKUPS FK
def get_lookup_provincia(q):
    rows = _fetchall(
        'SELECT id, "pro_provincia" FROM "app_core_provincia"'
        ' WHERE UPPER("pro_provincia") LIKE UPPER(%s)'
        ' ORDER BY "pro_provincia" LIMIT 10',
        (f'%{q}%',)
    )
    return [{"id": r[0], "nombre": str(r[1])} for r in rows]


def get_lookup_localidad(q, provincia_id=None):
    params = [f'%{q}%']
    sql = ('SELECT id, "loc_nombre" FROM "app_core_localidad"'
           ' WHERE UPPER("loc_nombre") LIKE UPPER(%s)')
    if provincia_id:
        sql += ' AND "loc_provincia_id" = %s'
        params.append(int(provincia_id))
    sql += ' ORDER BY "loc_nombre" LIMIT 10'
    rows = _fetchall(sql, params)
    return [{"id": r[0], "nombre": str(r[1])} for r in rows]


def get_all_tipoidentidad():
    rows = _fetchall(
        'SELECT id, "tid_tipo_identidad" FROM "app_gbl_tipoidentidad"'
        ' ORDER BY "tid_tipo_identidad"'
    )
    return [{"id": r[0], "nombre": str(r[1])} for r in rows]


def get_all_tipopersona():
    rows = _fetchall(
        'SELECT id, "tpe_tipo_persona" FROM "app_gbl_tipopersona"'
        ' ORDER BY "tpe_tipo_persona"'
    )
    return [{"id": r[0], "nombre": str(r[1])} for r in rows]


def get_nombre_by_id(tabla, col, id_val):
    if not id_val:
        return ''
    try:
        row = _fetchone(f'SELECT "{col}" FROM "{tabla}" WHERE id = %s', (int(id_val),))
        return str(row[0]) if row else ''
    except Exception:
        return ''
