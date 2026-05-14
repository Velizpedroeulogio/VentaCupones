from datetime import datetime
from django.db import connection


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
    for cand in [f"Evn{str(evn).zfill(5)}_02a.jpeg",
                 f"Evn{str(evn).zfill(5)}_01.jpeg"]:
        if os.path.exists(os.path.join(img_dir, cand)):
            return f"{base}/{cand}"
    return ""


def get_imagen_sponsor(evn, static_url="/static/"):
    import os
    base = f"{static_url}ventas/img"
    img_dir = os.path.join("static", "ventas", "img")
    cand = f"Evn{str(evn).zfill(5)}_02b.jpeg"
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
    """
    Recupera el registro de PVT_SORT vigente para hoy.
    Toma la primera PVT_FCHX <= hoy (la más reciente definición).
    """
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
    return {
        "pvt_fchx": row[0],
        "pvt_fchd": row[1],
        "pvt_fchh": row[2],
        "precios":  precios,
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
        'SELECT A."Srt_Nro", B."SRT_NUM", B."SRT_PRE1", B."SRT_PRE2"'
        '  FROM "SrtFchNum" A'
        '  LEFT JOIN "SORTEOS" B'
        '    ON B."EVN_NUM" = A."Evn_Num" AND B."SRT_NUM" = A."Srt_Rela"'
        ' WHERE A."Evn_Num" = %s AND A."Srt_Fcha" = %s'
        ' ORDER BY A."Srt_Nro"',
        (evn, int(fecha))
    )
    return [
        {"nro": str(r[0] or ""), "pre1": str(r[2] or ""), "pre2": str(r[3] or "")}
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
