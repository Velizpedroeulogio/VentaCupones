import os
import hmac as _hmac_mod
import hashlib
from datetime import datetime
from django.db import connection, transaction

_KEY1 = os.environ.get("GBYL_KEY1", "dvtcksqonz")
_KEY2 = os.environ.get("GBYL_KEY2", "ABCDEFGHIJ")
_CUPON_HMAC_KEY     = os.environ.get("CUPON_HMAC_KEY", "")
_WA_PHONE_NUMBER_ID = os.environ.get("WA_PHONE_NUMBER_ID", "")
_WA_ACCESS_TOKEN    = os.environ.get("WA_ACCESS_TOKEN", "")


def calcular_hmac_cupon(evn, sec):
    """Devuelve 8 caracteres hex derivados de (evn, sec) con clave secreta CUPON_HMAC_KEY.
    Si la clave no está configurada devuelve cadena vacía."""
    if not _CUPON_HMAC_KEY:
        return ""
    msg = f"{int(evn):05d}{int(sec):06d}".encode()
    return _hmac_mod.new(_CUPON_HMAC_KEY.encode(), msg, hashlib.sha256).hexdigest()[:8]


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
        'SELECT A."EVN_DSC", B."ENT_DSC"'
        ' FROM "EVN_DEF" A'
        ' LEFT JOIN "ENT_DEF" B ON B."ENT_NUM" = A."ENT_NUM"'
        ' WHERE A."EVN_NUM" = %s',
        (evn,)
    )
    if row:
        return {'evento': str(row[0] or ''), 'entidad': str(row[1] or '')}
    return {'evento': '', 'entidad': ''}


def get_nombres_meta(evn):
    return get_evento(evn)


# ------------------------------------------------------------------ EVENTO DEFAULTS
def get_evento_msgqr(evn):
    row = _fetchone('SELECT "EVN_MSGQR" FROM "EVN_DEF" WHERE "EVN_NUM" = %s', (evn,))
    return str(row[0] or '') if row else ''


def check_qr_habilitado(evn):
    """Retorna None si OK, o string de error si el servicio no está disponible."""
    from datetime import date
    hoy = date.today()
    row = _fetchone(
        'SELECT "EVN_ESTADO","EVN_FCHDES","EVN_FCHHAS" FROM "EVN_DEF" WHERE "EVN_NUM"=%s',
        (evn,)
    )
    if not row:
        return None
    estado, fch_des, fch_has = row
    estado = str(estado or 'H').strip()
    if estado == 'B':
        return "Servicio bloqueado"
    if fch_des and hoy < fch_des:
        return f"Servicio no disponible hasta el {fch_des.strftime('%d/%m/%Y')}"
    if fch_has and hoy > fch_has:
        return f"Servicio vencido el {fch_has.strftime('%d/%m/%Y')}"
    return None


def get_evento_defaults(evn):
    row = _fetchone(
        'SELECT "EVN_DFTCALL","EVN_DFTBARR","EVN_DFTPROV","EVN_DFTLOCA",'
        '       "EVN_DFTTID","EVN_DFTTPE","EVN_DFTCPOS"'
        ' FROM "EVN_DEF" WHERE "EVN_NUM" = %s',
        (evn,)
    )
    if not row:
        return {}
    return {
        'per_calle':             str(row[0] or ''),
        'per_barrio':            str(row[1] or ''),
        '_prv_desc':             str(row[2] or ''),
        '_loc_desc':             str(row[3] or ''),
        'per_tipo_identidad_id': str(row[4] or ''),
        'per_tipo_persona_id':   str(row[5] or ''),
        'per_codigo_postal':     str(row[6] or ''),
    }


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
        'SELECT "USR_NOMB","USR_PWDX","USR_ESTD","USR_FCHD","USR_FCHH","USR_TUSR"'
        ' FROM "USR_VTAS"'
        ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
        (evn, str(usuario or "").strip())
    )
    if not row:
        return False, "", "Usuario no encontrado"

    nombre, pwd_enc, estd, fchd, fchh, tusr = row

    if str(tusr or '').strip() != 'V':
        return False, "", "No es usuario vendedor"

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
        '       "PVT_CHN6","PVT_CHN7","PVT_CHN8","PVT_CHN9",'
        '       "PVT_BURL","PVT_WMSG","PVT_EMSJ","PVT_WPRO"'
        ' FROM "PVT_SORT"'
        ' WHERE "PVT_EVN" = %s AND "PVT_FCHX" <= %s'
        ' ORDER BY "PVT_FCHX" DESC'
        ' LIMIT 1',
        (evn, hoy)
    )
    if not row:
        return None
    precios = {}
    for i, val in enumerate(row[3:12], start=1):
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
        "burl":     str(row[12] or ""),
        "wmsg":     str(row[13] or ""),
        "emsj":     str(row[14] or ""),
        "wpro":     str(row[15] or ""),
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


# ------------------------------------------------------------------ TOPE VENTAS
def check_tope_ventas(evn, usuario):
    """
    Retorna {tope, count, bloqueado}.
    tope=0 significa sin límite configurado.
    Usa USR_TOPVTA del vendedor; si es 0 usa EVN_TOPVTA del evento.
    """
    row = _fetchone(
        'SELECT "USR_TOPVTA" FROM "USR_VTAS"'
        ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
        (evn, str(usuario or '').strip())
    )
    tope = int(row[0]) if row and row[0] else 0

    if tope == 0:
        row_evn = _fetchone(
            'SELECT "EVN_TOPVTA" FROM "EVN_DEF" WHERE "EVN_NUM" = %s', (evn,)
        )
        tope = int(row_evn[0]) if row_evn and row_evn[0] else 0

    if tope == 0:
        return {'tope': 0, 'count': 0, 'bloqueado': False}

    count_row = _fetchone(
        'SELECT COUNT(*) FROM "MDP_MOV"'
        ' WHERE "EVN_NUM" = %s AND "VEN_COD" = %s AND "PRD_ID" = 1 AND "MDP_ESTD" = \'I\'',
        (evn, str(usuario or '').strip())
    )
    count = int(count_row[0]) if count_row else 0
    return {'tope': tope, 'count': count, 'bloqueado': count >= tope}


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
            "mtz":  str(r[3] or ""),
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
            ' WHERE "EVNC_NUM" = %s AND "EVNC_SEC" = %s AND "EVNC_EST" IN (\'P\', \'X\')',
            ('X', str(usuario or ''), evn, int(sec))
        )
        return cur.rowcount > 0


def vender_cupon(evn, sec, usuario, nid=None, nom=None, dom=None, loc=None, ref=None, fpgo=None, precio=0):
    from datetime import date, datetime
    hoy   = date.today()
    ahora = datetime.now().time()
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                'UPDATE "EVNC_CAR"'
                ' SET "EVNC_EST"=%s,"EVNC_VEN"=%s,"EVNC_TIME"=NOW(),'
                '     "EVNC_NID"=%s,"EVNC_NOM"=%s,"EVNC_DOM"=%s,"EVNC_LOC"=%s,"EVNC_REF"=%s,'
                '     "EVNC_FPGO"=%s'
                ' WHERE "EVNC_NUM"=%s AND "EVNC_SEC"=%s',
                ('V', str(usuario or ''), nid, nom, dom, loc, ref, fpgo, evn, int(sec))
            )
            if cur.rowcount == 0:
                return False
            cur.execute(
                'INSERT INTO "MDP_MOV"'
                ' ("MDP_FCHA","MDP_HORA","PRD_ID","EVN_NUM","VEN_COD","CDM_ID",'
                '  "MDP_VALO","MDP_ACCI","MDP_ESTD","MDP_CPTE","MDP_FPGO","MDP_NID")'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (hoy, ahora, 1, evn, str(usuario or ''), 1,
                 precio, 'C', 'I', str(sec).zfill(6), fpgo, nid)
            )
            return True


# ------------------------------------------------------------------ ADMIN
def validate_admin_user(evn, usuario, pwd):
    row = _fetchone(
        'SELECT "USR_NOMB","USR_PWDX","USR_ESTD","USR_TUSR"'
        ' FROM "USR_VTAS"'
        ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
        (evn, str(usuario or '').strip())
    )
    if not row:
        return False, '', 'Usuario no encontrado'
    nombre, pwd_enc, estd, tusr = row
    if estd != 'A':
        return False, '', 'Usuario no habilitado'
    if str(tusr or '').strip() != 'A':
        return False, '', 'No es usuario administrativo'
    if encriptar_pwd(pwd) != str(pwd_enc or ''):
        return False, '', 'Contraseña incorrecta'
    return True, str(nombre or ''), ''


def get_rendiciones_admin(evn, desde=None, hasta=None):
    params = [evn, 2]
    where_extra = ''
    if desde and hasta:
        where_extra += ' AND M."MDP_FCHA" BETWEEN %s AND %s'
        params += [desde, hasta]
    rows = _fetchall(
        'SELECT M."MDP_FCHA", M."VEN_COD", M."MDP_CPTE",'
        '       M."MDP_VALO", M."MDP_ESTD", M."MDP_REFE",'
        '       COALESCE(U."USR_NOMB", \'\') AS usr_nomb'
        '  FROM "MDP_MOV" M'
        '  LEFT JOIN "USR_VTAS" U'
        '    ON U."USR_EVNX" = M."EVN_NUM" AND U."USR_IDEU" = M."VEN_COD"'
        ' WHERE M."EVN_NUM" = %s AND M."PRD_ID" = %s'
        + where_extra +
        ' ORDER BY M."MDP_FCHA" DESC, M."MDP_HORA" DESC',
        params
    )
    result = []
    for r in rows:
        fcha = r[0]
        result.append({
            'fecha_fmt': fcha.strftime('%d.%m.%y') if fcha else '',
            'ven_cod':   str(r[1] or ''),
            'cpte':      str(r[2] or ''),
            'valo':      float(r[3]) if r[3] is not None else 0.0,
            'estd':      str(r[4] or ''),
            'refe':      str(r[5] or ''),
            'usr_nomb':  str(r[6] or ''),
        })
    return result


def certificar_rendicion(evn, usuario_vend, nro_rend, ref_banco):
    """
    Certifica una rendición: PRD=1 X→R y PRD=2 X→R con MDP_REFE=ref_banco.
    Retorna (ok, mensaje).
    """
    nro_fmt = str(nro_rend or '').strip().zfill(4)
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                'SELECT "ID", "MDP_IREF" FROM "MDP_MOV"'
                ' WHERE "EVN_NUM"=%s AND "VEN_COD"=%s AND "PRD_ID"=2'
                '   AND "MDP_CPTE"=%s AND "MDP_ESTD"=\'X\'',
                (evn, str(usuario_vend or '').strip(), nro_fmt)
            )
            row = cur.fetchone()
            if not row:
                return False, 'Rendición no encontrada o ya certificada'
            comision = float(row[1]) if row[1] is not None else 0.0
            cur.execute(
                'UPDATE "MDP_MOV" SET "MDP_ESTD"=\'R\''
                ' WHERE "EVN_NUM"=%s AND "VEN_COD"=%s AND "PRD_ID"=1'
                '   AND "MDP_ESTD"=\'X\' AND "MDP_REFE"=%s',
                (evn, str(usuario_vend or '').strip(), nro_fmt)
            )
            cur.execute(
                'UPDATE "MDP_MOV" SET "MDP_ESTD"=\'R\', "MDP_REFE"=%s'
                ' WHERE "EVN_NUM"=%s AND "VEN_COD"=%s AND "PRD_ID"=2'
                '   AND "MDP_ESTD"=\'X\' AND "MDP_CPTE"=%s',
                (str(ref_banco or '').strip(), evn,
                 str(usuario_vend or '').strip(), nro_fmt)
            )
            from datetime import date, datetime
            hoy   = date.today()
            ahora = datetime.now().time()
            cur.execute(
                'INSERT INTO "MDP_MOV"'
                ' ("MDP_FCHA","MDP_HORA","PRD_ID","EVN_NUM","VEN_COD","CDM_ID",'
                '  "MDP_VALO","MDP_ACCI","MDP_ESTD","MDP_CPTE","MDP_REFE")'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (hoy, ahora, 3, evn, str(usuario_vend or '').strip(), 1,
                 comision, 'R', 'R', nro_fmt, str(ref_banco or '').strip())
            )
            return True, 'OK'


# ------------------------------------------------------------------ RENDICION
def get_rendicion_data(evn, usuario, desde=None, hasta=None, fpgo=None):
    """Datos de la liquidación previa: ventas I filtradas + totales + comisión."""
    row = _fetchone(
        'SELECT "USR_PCJCOM","USR_NRND" FROM "USR_VTAS"'
        ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s',
        (evn, str(usuario or '').strip())
    )
    pcjcom   = float(row[0]) if row and row[0] else 0.0
    nro_rend = (int(row[1]) if row and row[1] else 0) + 1

    params = [evn, str(usuario), 1, 'I']
    where_extra = ''
    if desde and hasta:
        where_extra += ' AND M."MDP_FCHA" BETWEEN %s AND %s'
        params += [desde, hasta]
    if fpgo == 'blank':
        where_extra += ' AND (M."MDP_FPGO" IS NULL OR M."MDP_FPGO" = \'\')'
    elif fpgo:
        where_extra += ' AND M."MDP_FPGO" = %s'
        params.append(fpgo)

    rows = _fetchall(
        'SELECT M."MDP_FCHA", M."MDP_CPTE", M."MDP_FPGO", M."MDP_VALO",'
        '       M."MDP_NID", COALESCE(P."per_nombre", \'\') AS per_nombre'
        '  FROM "MDP_MOV" M'
        '  LEFT JOIN "app_gbl_persona" P ON P."per_numero_identidad" = M."MDP_NID"'
        ' WHERE M."EVN_NUM" = %s AND M."VEN_COD" = %s AND M."PRD_ID" = %s AND M."MDP_ESTD" = %s'
        + where_extra +
        ' ORDER BY M."MDP_FCHA", M."MDP_HORA"',
        params
    )
    ventas = []
    total  = 0.0
    for r in rows:
        valo = float(r[3]) if r[3] is not None else 0.0
        total += valo
        fcha  = r[0]
        ventas.append({
            'fecha_fmt':  fcha.strftime('%d.%m.%y') if fcha else '',
            'cpte':       str(r[1] or ''),
            'fpgo':       str(r[2] or ''),
            'valo':       valo,
            'nid':        str(r[4] or ''),
            'per_nombre': str(r[5] or ''),
        })
    comision = round(total * pcjcom / 100, 2)
    neto     = round(total - comision, 2)
    return {
        'ventas':       ventas,
        'total':        total,
        'pcjcom':       pcjcom,
        'comision':     comision,
        'neto':         neto,
        'nro_rend':     nro_rend,
        'nro_rend_fmt': str(nro_rend).zfill(4),
    }


def confirmar_rendicion(evn, usuario, desde=None, hasta=None, fpgo=None):
    """
    Confirma la rendición en una transacción atómica:
    actualiza ventas I→X con MDP_REFE=nro, graba PRD=2, incrementa USR_NRND.
    Retorna nro_rend_fmt o None si no había ventas.
    """
    from datetime import date, datetime
    hoy   = date.today()
    ahora = datetime.now().time()

    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                'SELECT "USR_NRND","USR_PCJCOM" FROM "USR_VTAS"'
                ' WHERE "USR_EVNX" = %s AND "USR_IDEU" = %s FOR UPDATE',
                (evn, str(usuario or '').strip())
            )
            row      = cur.fetchone()
            nro_rend = (int(row[0]) if row and row[0] else 0) + 1
            pcjcom   = float(row[1]) if row and row[1] else 0.0
            nro_fmt  = str(nro_rend).zfill(4)

            params_w = [evn, str(usuario), 1, 'I']
            where_extra = ''
            if desde and hasta:
                where_extra += ' AND "MDP_FCHA" BETWEEN %s AND %s'
                params_w += [desde, hasta]
            if fpgo == 'blank':
                where_extra += ' AND ("MDP_FPGO" IS NULL OR "MDP_FPGO" = \'\')'
            elif fpgo:
                where_extra += ' AND "MDP_FPGO" = %s'
                params_w.append(fpgo)

            cur.execute(
                'SELECT COUNT(*), COALESCE(SUM("MDP_VALO"),0) FROM "MDP_MOV"'
                ' WHERE "EVN_NUM"=%s AND "VEN_COD"=%s AND "PRD_ID"=%s AND "MDP_ESTD"=%s'
                + where_extra, params_w
            )
            r2    = cur.fetchone()
            count = int(r2[0]) if r2 else 0
            total = float(r2[1]) if r2 else 0.0
            if count == 0:
                return None

            comision = round(total * pcjcom / 100, 2)
            neto     = round(total - comision, 2)
            cur.execute(
                'UPDATE "MDP_MOV" SET "MDP_ESTD"=%s,"MDP_REFE"=%s,"MDP_IREF"="MDP_VALO"*%s/100.0'
                ' WHERE "EVN_NUM"=%s AND "VEN_COD"=%s AND "PRD_ID"=%s AND "MDP_ESTD"=%s'
                + where_extra,
                ['X', nro_fmt, pcjcom] + params_w
            )
            cur.execute(
                'INSERT INTO "MDP_MOV"'
                ' ("MDP_FCHA","MDP_HORA","PRD_ID","EVN_NUM","VEN_COD","CDM_ID",'
                '  "MDP_VALO","MDP_IREF","MDP_ACCI","MDP_ESTD","MDP_CPTE")'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (hoy, ahora, 2, evn, str(usuario or ''), 1,
                 neto, comision, 'R', 'X', nro_fmt)
            )
            cur.execute(
                'UPDATE "USR_VTAS" SET "USR_NRND"=%s'
                ' WHERE "USR_EVNX"=%s AND "USR_IDEU"=%s',
                (nro_rend, evn, str(usuario or '').strip())
            )
            return nro_fmt


# ------------------------------------------------------------------ QR AUTO-ASIGNACION
_QR_TABLA = [
    #  ini  fin   [dig 0-2, dig 3-4, dig 5-7, dig 8-9]
    (0,  14, [2, 3, 6, 9]),
    (15, 29, [9, 6, 3, 2]),
    (30, 44, [6, 9, 2, 3]),
    (45, 59, [3, 2, 9, 6]),
]


def get_cantidad_qr(segundo, ultimo_digito):
    d = int(ultimo_digito)
    for ini, fin, cant in _QR_TABLA:
        if ini <= segundo <= fin:
            if d in (0, 1, 2): return cant[0]
            if d in (3, 4):    return cant[1]
            if d in (5, 6, 7): return cant[2]
            return cant[3]
    return 2


def asignar_cupon_qr(evn, nid, nombre, fecha_nac, celular, qr_usuario='codigoQR'):
    """
    Determina cantidad por tabla minuto/dígito, busca cupón, lo vende a qr_usuario.
    Retorna (sec, cartones, cantidad, error_msg).
    """
    from datetime import date, datetime
    hoy   = date.today()
    ahora = datetime.now().time()

    # Validar estado y fechas habilitadas del evento
    evn_ctrl = _fetchone(
        'SELECT "EVN_ESTADO","EVN_FCHDES","EVN_FCHHAS" FROM "EVN_DEF" WHERE "EVN_NUM"=%s',
        (evn,)
    )
    if evn_ctrl:
        estado, fch_des, fch_has = evn_ctrl
        estado = str(estado or 'H').strip()
        if estado == 'B':
            return None, None, None, "Servicio bloqueado"
        if fch_des and hoy < fch_des:
            return None, None, None, f"Servicio no disponible hasta el {fch_des.strftime('%d/%m/%Y')}"
        if fch_has and hoy > fch_has:
            return None, None, None, f"Servicio vencido el {fch_has.strftime('%d/%m/%Y')}"

    segundo    = datetime.now().second
    ultimo_dig = int(str(abs(int(nid)))[-1])
    cantidad   = get_cantidad_qr(segundo, ultimo_dig)

    pvt = get_pvt_sort(evn)
    if not pvt:
        return None, None, cantidad, "Sin configuración de venta vigente"
    if cantidad not in pvt.get('rangos', {}):
        return None, None, cantidad, f"Sin rango configurado para {cantidad} cartones"

    rango     = pvt['rangos'][cantidad]
    secuencias = get_secuencias_disponibles(evn, rango['scd'], rango['sch'])
    if not secuencias:
        return None, None, cantidad, "Sin cupones disponibles"

    sec    = secuencias[0]
    precio = pvt['precios'].get(cantidad, 0)

    # Persona: usar existente o guardar nueva con defaults del evento
    persona = get_persona(nid)
    if persona:
        nom     = persona.get('per_nombre') or nombre
        loc_txt = get_nombre_by_id('app_core_localidad', 'loc_nombre', persona.get('per_localidad_id'))
        prv_txt = get_nombre_by_id('app_core_provincia', 'pro_provincia', persona.get('per_provincia_id'))
        def v(k): return persona.get(k) or ''
        dom = f"{v('per_barrio')}|{v('per_calle')}|{v('per_puerta')}|{v('per_piso')}|{v('per_depto')}|"
        loc = f"{prv_txt}|{loc_txt}|{v('per_codigo_postal')}|"
        ref = f"{v('per_celular')}|{v('per_email')}|{v('per_telefono')}|||"
    else:
        nom     = nombre
        defs    = get_evento_defaults(evn)
        prv_id  = get_or_create_provincia(defs.get('_prv_desc', ''))
        loc_id  = get_or_create_localidad(defs.get('_loc_desc', ''), prv_id)
        tid     = int(defs.get('per_tipo_identidad_id') or 1)
        tpe     = int(defs.get('per_tipo_persona_id') or 1)
        calle   = defs.get('per_calle', '')
        barrio  = defs.get('per_barrio', '')
        cpos    = defs.get('per_codigo_postal', '')
        prv_txt = defs.get('_prv_desc', '')
        loc_txt = defs.get('_loc_desc', '')
        try:
            with connection.cursor() as cur:
                cur.execute(
                    'INSERT INTO "app_gbl_persona"'
                    ' ("per_numero_identidad","per_fecha_nac","per_nombre",'
                    '  "per_calle","per_barrio","per_codigo_postal","per_celular",'
                    '  "per_localidad_id","per_provincia_id",'
                    '  "per_tipo_identidad_id","per_tipo_persona_id")'
                    ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (int(nid), fecha_nac or None, nombre,
                     calle, barrio, cpos, celular,
                     loc_id, prv_id, tid, tpe)
                )
        except Exception:
            pass
        dom = f"{barrio}|{calle}|||"
        loc = f"{prv_txt}|{loc_txt}|{cpos}|"
        ref = f"{celular}||||"

    # Vender atómicamente (verifica disponibilidad en el UPDATE)
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                'UPDATE "EVNC_CAR"'
                ' SET "EVNC_EST"=%s,"EVNC_VEN"=%s,"EVNC_TIME"=NOW(),'
                '     "EVNC_NID"=%s,"EVNC_NOM"=%s,"EVNC_DOM"=%s,"EVNC_LOC"=%s,"EVNC_REF"=%s,'
                '     "EVNC_FPGO"=%s'
                ' WHERE "EVNC_NUM"=%s AND "EVNC_SEC"=%s AND ' + _EST_DISPONIBLE,
                ('V', str(qr_usuario), int(nid), nom, dom, loc, ref, 'Q', evn, int(sec))
            )
            if cur.rowcount == 0:
                return None, None, cantidad, "El cupón ya no está disponible, intente nuevamente"
            cur.execute(
                'INSERT INTO "MDP_MOV"'
                ' ("MDP_FCHA","MDP_HORA","PRD_ID","EVN_NUM","VEN_COD","CDM_ID",'
                '  "MDP_VALO","MDP_ACCI","MDP_ESTD","MDP_CPTE","MDP_FPGO","MDP_NID")'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (hoy, ahora, 1, evn, str(qr_usuario), 1,
                 precio, 'C', 'I', str(sec).zfill(6), 'Q', int(nid))
            )

    cartones = get_cartones_cupon(evn, sec)

    # Armar URL del visor con INF_ADIC (ya poblado desde SQLite via TransferirINF_URL)
    try:
        dv_row = _fetchone(
            'SELECT "INF_DV1","INF_DV2","INF_ADIC" FROM "INF_URL" WHERE "INF_EVN"=%s AND "INF_SEC"=%s',
            (evn, int(sec))
        )
        if dv_row:
            dv1  = str(dv_row[0] or '')
            dv2  = str(dv_row[1] or '')
            adic = str(dv_row[2] or '')
            url_visor = ('https://visor-gbl-production.up.railway.app/?id='
                         + str(evn).zfill(5) + str(sec).zfill(6) + dv1 + dv2 + adic)
            texto_msg = (f'se te asignó el cupón {str(sec).zfill(6)} '
                         f'PARA EL BINGO {url_visor}')
            registrar_msg_proc('ASIGNA-QR', celular, texto_msg, evn=evn, sec=int(sec))
            if _WA_PHONE_NUMBER_ID and celular:
                enviar_notif_meta(evn, sec, celular, nom)
    except Exception:
        pass

    return sec, cartones, cantidad, None


# ------------------------------------------------------------------ MOVIMIENTOS
def get_prd_desc(prd):
    row = _fetchone('SELECT "PRD_DSCR" FROM "PRD_MOV" WHERE "ID" = %s', (int(prd),))
    return str(row[0]) if row else ''


PAGE_SIZE = 50

def get_movimientos(evn, usuario, prd, desde=None, hasta=None, fpgo=None, estd=None, page=1):
    params = [evn, str(usuario), int(prd)]
    where_extra = ''
    if desde and hasta:
        where_extra += ' AND M."MDP_FCHA" BETWEEN %s AND %s'
        params += [desde, hasta]
    if fpgo == 'blank':
        where_extra += ' AND (M."MDP_FPGO" IS NULL OR M."MDP_FPGO" = \'\')'
    elif fpgo:
        where_extra += ' AND M."MDP_FPGO" = %s'
        params.append(fpgo)
    if estd:
        where_extra += ' AND M."MDP_ESTD" = %s'
        params.append(estd)
    base_from = (
        '  FROM "MDP_MOV" M'
        '  LEFT JOIN "app_gbl_persona" P ON P."per_numero_identidad" = M."MDP_NID"'
        ' WHERE M."EVN_NUM" = %s AND M."VEN_COD" = %s AND M."PRD_ID" = %s'
        + where_extra
    )
    count_row = _fetchone('SELECT COUNT(*)' + base_from, params)
    total = int(count_row[0]) if count_row else 0
    offset = (max(1, page) - 1) * PAGE_SIZE
    rows = _fetchall(
        'SELECT M."MDP_FCHA", M."MDP_ACCI", M."MDP_CPTE", M."MDP_VALO",'
        '       M."MDP_ESTD", M."MDP_REFE", M."MDP_NID", M."MDP_FPGO",'
        '       COALESCE(P."per_nombre", \'\') AS per_nombre'
        + base_from +
        ' ORDER BY M."MDP_FCHA", M."MDP_HORA"'
        ' LIMIT %s OFFSET %s',
        params + [PAGE_SIZE, offset]
    )
    result = []
    for r in rows:
        fcha = r[0]
        result.append({
            'fcha':       fcha,
            'fecha_fmt':  fcha.strftime('%d.%m.%y') if fcha else '',
            'acci':       str(r[1] or ''),
            'cpte':       str(r[2] or ''),
            'valo':       float(r[3]) if r[3] is not None else 0.0,
            'estd':       str(r[4] or ''),
            'refe':       str(r[5] or ''),
            'fpgo':       str(r[7] or ''),
            'per_nombre': str(r[8] or ''),
        })
    return result, total


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


# ------------------------------------------------------------------ NOTIFICACIONES
def _calc_mod10(txt):
    s = ''.join(c for c in str(txt or '') if c.isdigit())
    if not s:
        return 0
    suma, fact = 0, 2
    for c in reversed(s):
        val = int(c) * fact
        if val > 9:
            val = val // 10 + val % 10
        suma += val
        fact = 1 if fact == 2 else 2
    return (10 - (suma % 10)) % 10


def _gen_url_id(evn, sec):
    s_evn = str(evn).zfill(5)
    s_sec = str(sec).zfill(6)
    dv1 = _calc_mod10(s_evn + s_sec)
    dv2 = _calc_mod10(str(dv1) + s_sec + s_evn)
    return f"{s_evn}{s_sec}{dv1}{dv2}"


def _enviar_whatsapp(celular, texto, wpro):
    import os, re, requests as req
    digits = re.sub(r'\D', '', celular)
    if not digits.startswith('54'):
        digits = '54' + digits
    if wpro == 'T':
        sid   = os.environ.get('TWILIO_SID', '')
        token = os.environ.get('TWILIO_TOKEN', '')
        from_ = os.environ.get('TWILIO_FROM', '')
        if not sid or not token or not from_:
            return
        req.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
            auth=(sid, token),
            data={'From': f'whatsapp:{from_}', 'To': f'whatsapp:+{digits}', 'Body': texto},
            timeout=10,
        )
    else:  # 'C' = CallMeBot
        key = os.environ.get('CALLMEBOT_KEY', '')
        if not key:
            return
        req.get(
            'https://api.callmebot.com/whatsapp.php',
            params={'phone': digits, 'text': texto, 'apikey': key},
            timeout=10,
        )


def _enviar_email(to_addr, subject, body):
    import os, smtplib, logging
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    log = logging.getLogger(__name__)
    host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('SMTP_PORT', '465'))
    user = os.environ.get('SMTP_USER', '')
    pwd  = os.environ.get('SMTP_PASS', '')
    log.info("SMTP host=%s port=%s user=%r pwd_set=%s", host, port, user, bool(pwd))
    if not user or not pwd:
        log.warning("SMTP sin credenciales — email NO enviado")
        return
    msg = MIMEMultipart()
    msg['From']    = user
    msg['To']      = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    if port == 587:
        with smtplib.SMTP(host, port) as s:
            s.ehlo()
            s.starttls()
            s.login(user, pwd)
            s.sendmail(user, to_addr, msg.as_string())
    else:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(user, pwd)
            s.sendmail(user, to_addr, msg.as_string())
    log.info("SMTP OK enviado a %s", to_addr)


def _enviar_whatsapp_meta(celular, nombre, num_cupon, entidad, evento, url_id):
    # Plantilla: bingosabg
    # Header {{1}}=entidad
    # Body   {{1}}=nombre  {{2}}=evento  {{3}}=num_cupon
    # Botón CTA URL dinámica: sufijo url_id
    import re
    import requests as req
    if not _WA_PHONE_NUMBER_ID or not _WA_ACCESS_TOKEN:
        raise ValueError("WA_PHONE_NUMBER_ID o WA_ACCESS_TOKEN no configurados")
    digits = re.sub(r'\D', '', celular)
    if digits.startswith('549'):
        pass                               # 5493816401776 → ok
    elif digits.startswith('54'):
        digits = '549' + digits[2:]        # 543816401776  → 5493816401776
    elif digits.startswith('0'):
        digits = '549' + digits[1:]        # 03816401776   → 5493816401776
    else:
        digits = '549' + digits            # 3816401776    → 5493816401776
    payload = {
        "messaging_product": "whatsapp",
        "to": digits,
        "type": "template",
        "template": {
            "name": "bingosabg",
            "language": {"code": "es_AR"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {"type": "text", "text": entidad}
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": nombre},
                        {"type": "text", "text": evento},
                        {"type": "text", "text": num_cupon},
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": url_id}]
                }
            ]
        }
    }
    resp = req.post(
        f"https://graph.facebook.com/v20.0/{_WA_PHONE_NUMBER_ID}/messages",
        headers={
            "Authorization": f"Bearer {_WA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    if resp.status_code not in (200, 201):
        raise ValueError(f"Meta API {resp.status_code}: {resp.text[:200]}")


def enviar_notif_meta(evn, sec, celular, nombre):
    """Envía plantilla bingo_abg via Meta Graph API y registra en MSG_PROC. No lanza excepciones."""
    import logging
    log = logging.getLogger(__name__)
    num_cupon = str(sec).zfill(6)
    try:
        evn_info     = get_nombres_meta(evn)
        entidad      = evn_info['entidad']
        evento       = evn_info['evento']
        pvt          = get_pvt_sort(evn)
        fecha_sorteo = fmt_fecha(pvt['pvt_fchd']) if pvt and pvt.get('pvt_fchd') else ''
        dv_row = _fetchone(
            'SELECT "INF_DV1","INF_DV2","INF_ADIC" FROM "INF_URL"'
            ' WHERE "INF_EVN"=%s AND "INF_SEC"=%s',
            (evn, int(sec))
        )
        if dv_row:
            dv1  = str(dv_row[0] or '')
            dv2  = str(dv_row[1] or '')
            adic = str(dv_row[2] or '')
            url_id = str(evn).zfill(5) + num_cupon + dv1 + dv2 + adic
        else:
            url_id = _gen_url_id(evn, sec)
        pvt_burl = str(pvt.get('burl') or 'https://visor-gbl-production.up.railway.app').rstrip('/')
        url_full = f"{pvt_burl}/?id={url_id}"
        txto_msg = (
            f"{entidad} - Cupón para Sorteo\n\n"
            f"¡Felicidades {nombre}! Ya estás participando en el sorteo {evento}. "
            f"Tu cupón es el \"{num_cupon}\". ¡Mucha suerte!\n\n"
            f"Ver mi cupón: {url_full}"
        )
        _enviar_whatsapp_meta(celular, nombre, num_cupon, entidad, evento, url_id)
        registrar_msg_proc('META-WA', f'{celular}|', txto_msg, evn=evn, sec=int(sec))
        log.info("META-WA OK evn=%s sec=%s cel=%s", evn, sec, celular)
    except Exception as e:
        log.error("META-WA error evn=%s sec=%s: %s", evn, sec, e)
        registrar_msg_proc('META-WA', f'{celular}|', f'bingo_abg {nombre} cupon {num_cupon}',
                           evn=evn, sec=int(sec), erro=str(e)[:500])
        raise


def get_msg_idpr_opciones(evn):
    rows = _fetchall(
        'SELECT DISTINCT "MSG_IDPR" FROM "MSG_PROC" WHERE "MSG_EVN"=%s AND "MSG_IDPR" IS NOT NULL ORDER BY 1',
        (evn,)
    )
    return [str(r[0]) for r in rows if r[0]]


def get_msg_proc(evn, fecha=None, idpr=None, mrka=None):
    conds  = ['"MSG_EVN" = %s']
    params = [evn]
    if fecha:
        conds.append('"MSG_FCHA" = %s')
        params.append(fecha)
    if idpr:
        conds.append('"MSG_IDPR" = %s')
        params.append(idpr)
    if mrka == 'PX':
        conds.append("\"MSG_MRKA\" IN ('P','X')")
    elif mrka:
        conds.append('"MSG_MRKA" = %s')
        params.append(mrka)
    where = ' AND '.join(conds)
    rows = _fetchall(
        'SELECT "MSG_ID","MSG_FCHA","MSG_HORA","MSG_IDPR","MSG_SEC",'
        '       "MSG_REFE","MSG_TXTO","MSG_ERRO","MSG_MRKA"'
        ' FROM "MSG_PROC"'
        ' WHERE ' + where +
        ' ORDER BY "MSG_FCHA" DESC, "MSG_HORA" DESC'
        ' LIMIT 200',
        params
    )
    result = []
    for r in rows:
        refe   = str(r[5] or '')
        partes = refe.split('|')
        cel    = partes[0].strip() if len(partes) > 0 else ''
        mail   = partes[1].strip() if len(partes) > 1 else ''
        fcha   = r[1]
        result.append({
            'id':    r[0],
            'fecha': fcha.strftime('%d.%m.%y') if fcha else '',
            'hora':  str(r[2])[:5] if r[2] else '',
            'idpr':  str(r[3] or ''),
            'sec':   str(r[4]).zfill(6) if r[4] else '',
            'cel':   cel,
            'mail':  mail,
            'txto':  str(r[6] or ''),
            'erro':  str(r[7] or ''),
            'mrka':  str(r[8] or ''),
        })
    return result


def get_preview_plantilla(evn, msg_id):
    """Devuelve los datos para preview de plantilla Meta de un MSG_PROC."""
    row = _fetchone(
        'SELECT "MSG_REFE","MSG_SEC" FROM "MSG_PROC"'
        ' WHERE "MSG_ID"=%s AND "MSG_EVN"=%s',
        (msg_id, evn)
    )
    if not row:
        return None
    refe   = str(row[0] or '')
    sec    = int(row[1]) if row[1] else 0
    partes = refe.split('|')
    cel    = partes[0].strip() if partes else ''

    evn_info     = get_nombres_meta(evn)
    entidad      = evn_info['entidad']
    evento       = evn_info['evento']
    num_cupon    = str(sec).zfill(6)

    row_nom = _fetchone(
        'SELECT "EVNC_NOM" FROM "EVNC_CAR"'
        ' WHERE "EVNC_NUM"=%s AND "EVNC_SEC"=%s LIMIT 1',
        (evn, sec)
    )
    nombre = str(row_nom[0] or '') if row_nom else ''

    pvt          = get_pvt_sort(evn)
    burl         = str((pvt or {}).get('burl') or 'https://visor-gbl-production.up.railway.app').rstrip('/')
    fecha_sorteo = fmt_fecha(pvt['pvt_fchd']) if pvt and pvt.get('pvt_fchd') else ''

    dv_row = _fetchone(
        'SELECT "INF_DV1","INF_DV2","INF_ADIC" FROM "INF_URL"'
        ' WHERE "INF_EVN"=%s AND "INF_SEC"=%s',
        (evn, sec)
    )
    if dv_row:
        url_id = str(evn).zfill(5) + num_cupon + str(dv_row[0] or '') + str(dv_row[1] or '') + str(dv_row[2] or '')
    else:
        url_id = _gen_url_id(evn, sec)
    url = f"{burl}/?id={url_id}"

    return {
        'nombre':       nombre,
        'entidad':      entidad,
        'evento':       evento,
        'num_cupon':    num_cupon,
        'celular':      cel,
        'fecha_sorteo': fecha_sorteo,
        'url':          url,
    }


def reenviar_msg_proc(evn, msg_id, via):
    """Reenvía un MSG_PROC. via='M' email, via='W' whatsapp. Actualiza MSG_MRKA."""
    row = _fetchone(
        'SELECT "MSG_REFE","MSG_TXTO","MSG_SEC" FROM "MSG_PROC"'
        ' WHERE "MSG_ID"=%s AND "MSG_EVN"=%s',
        (msg_id, evn)
    )
    if not row:
        return False, 'Registro no encontrado'

    refe   = str(row[0] or '')
    txto   = str(row[1] or '')
    sec    = str(row[2] or '').zfill(6)
    partes = refe.split('|')
    cel    = partes[0].strip() if len(partes) > 0 else ''
    mail   = partes[1].strip() if len(partes) > 1 else ''

    try:
        if via == 'M':
            if not mail:
                return False, 'Sin dirección de email'
            _enviar_email(mail, f'Cupón N° {sec}', txto)
        elif via == 'T':
            if not cel:
                return False, 'Sin número de WhatsApp'
            sec_int = int(sec) if sec.isdigit() else 0
            row_evnc = _fetchone(
                'SELECT "EVNC_NOM" FROM "EVNC_CAR"'
                ' WHERE "EVNC_NUM"=%s AND "EVNC_SEC"=%s LIMIT 1',
                (evn, sec_int)
            )
            nombre_evnc = str(row_evnc[0] or '') if row_evnc else ''
            enviar_notif_meta(evn, sec_int, cel, nombre_evnc)
        else:
            if not cel:
                return False, 'Sin número de WhatsApp'
            pvt  = get_pvt_sort(evn)
            wpro = str(pvt.get('wpro') or 'C') if pvt else 'C'
            _enviar_whatsapp(cel, txto, wpro)
        with connection.cursor() as cur:
            cur.execute(
                'UPDATE "MSG_PROC" SET "MSG_MRKA"=%s WHERE "MSG_ID"=%s',
                ('E', msg_id)
            )
        return True, 'Enviado correctamente'
    except Exception as e:
        with connection.cursor() as cur:
            cur.execute(
                'UPDATE "MSG_PROC" SET "MSG_MRKA"=%s, "MSG_ERRO"=%s WHERE "MSG_ID"=%s',
                ('X', str(e)[:500], msg_id)
            )
        return False, str(e)


def registrar_msg_proc(idpr, refe, txto, evn=None, sec=None, erro=None):
    from datetime import date, datetime
    try:
        hoy   = date.today()
        ahora = datetime.now().time()
        with connection.cursor() as cur:
            cur.execute(
                'INSERT INTO "MSG_PROC"'
                ' ("MSG_FCHA","MSG_HORA","MSG_IDPR","MSG_EVN","MSG_SEC",'
                '  "MSG_REFE","MSG_TXTO","MSG_MRKA","MSG_ERRO")'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (hoy, ahora, str(idpr or '')[:30], evn, sec,
                 str(refe or '')[:200], str(txto or '')[:500],
                 'P', str(erro or '')[:500])
            )
    except Exception:
        pass


def enviar_notif_venta(evn, sec, persona, pvt):
    """Envía WhatsApp o email tras confirmar la venta. Nunca lanza excepciones."""
    import logging
    log = logging.getLogger(__name__)
    celular = email = texto = ''
    try:
        burl     = str(pvt.get('burl') or '').strip()
        wmsg_tpl = str(pvt.get('wmsg') or '').strip()
        emsj_tpl = str(pvt.get('emsj') or '').strip()
        wpro     = str(pvt.get('wpro') or 'M').strip()
        log.info("NOTIF evn=%s sec=%s wpro=%s burl=%s", evn, sec, wpro, burl)
        if wpro == 'W':
            nombre  = str(persona.get('per_nombre') or '')
            celular = str(persona.get('per_celular') or '').strip()
            if celular:
                enviar_notif_meta(evn, sec, celular, nombre)
            else:
                log.warning("NOTIF wpro=W pero persona sin celular")
            return
        if not burl or not wmsg_tpl:
            log.warning("NOTIF sin configurar: burl=%r wmsg=%r", burl, wmsg_tpl)
            return
        nombre  = str(persona.get('per_nombre') or '')
        cupon   = str(sec).zfill(6)
        celular = str(persona.get('per_celular') or '').strip()
        email   = str(persona.get('per_email')   or '').strip()
        log.info("NOTIF destino: email=%r celular=%r", email, celular)
        dv_row = _fetchone(
            'SELECT "INF_DV1","INF_DV2","INF_ADIC" FROM "INF_URL"'
            ' WHERE "INF_EVN"=%s AND "INF_SEC"=%s',
            (evn, int(sec))
        )
        if dv_row:
            url_id = str(evn).zfill(5) + str(sec).zfill(6) + str(dv_row[0] or '') + str(dv_row[1] or '') + str(dv_row[2] or '')
        else:
            url_id = _gen_url_id(evn, sec)
        url    = f"{burl.rstrip('/')}/?id={url_id}"
        texto  = wmsg_tpl.format(nombre=nombre, cupon=cupon, url=url)
        asunto = emsj_tpl.format(nombre=nombre, cupon=cupon, url=url) if emsj_tpl else f"Tu cupón N° {cupon}"
        if wpro == 'M':
            if email:
                _enviar_email(email, asunto, texto)
                log.info("NOTIF email enviado a %s", email)
            else:
                log.warning("NOTIF wpro=M pero persona sin email")
        else:
            if celular:
                _enviar_whatsapp(celular, texto, wpro)
                log.info("NOTIF WA enviado a %s", celular)
            elif email:
                _enviar_email(email, asunto, texto)
                log.info("NOTIF email enviado a %s", email)
            else:
                log.warning("NOTIF persona sin celular ni email")
    except Exception as e:
        log.error("NOTIF error: %s", e, exc_info=True)
        registrar_msg_proc(
            idpr='VENTAS-ENVIO',
            refe=f"{celular}|{email}",
            txto=texto,
            evn=evn,
            sec=sec,
            erro=str(e),
        )
