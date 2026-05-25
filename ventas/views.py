import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from . import services as svc


def _fmt_precio(valor):
    s = f"{float(valor):,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def login_view(request, evn):
    return render(request, "ventas/form1.html", {
        "evn":         evn,
        "evento_desc": svc.get_evento(evn),
        "img_evento":  svc.get_imagen_evento(evn),
        "bloqueo_msg": svc.check_qr_habilitado(evn),
    })


@csrf_exempt
def login_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    usuario = str(body.get("usuario", "")).strip()
    pwd     = str(body.get("pwd", "")).strip()

    if not usuario or not pwd:
        return JsonResponse({"ok": False, "error": "Datos incompletos"})

    ok, nombre, error = svc.validate_user(evn, usuario, pwd)
    if not ok:
        return JsonResponse({"ok": False, "error": error})

    request.session["evn"]     = evn
    request.session["usuario"] = usuario
    request.session["nombre"]  = nombre

    return JsonResponse({"ok": True, "nombre": nombre})


def principal(request, evn):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)

    pvt     = svc.get_pvt_sort(evn)
    fechas  = []
    precios_lista = []
    if pvt:
        fechas = svc.get_fechas_sorteo(evn, pvt["pvt_fchd"], pvt["pvt_fchh"])
        precios_lista = [
            {"chns": n, "precio_fmt": _fmt_precio(p)}
            for n, p in sorted(pvt["precios"].items())
        ]

    cupon_sec   = request.session.get("cupon_sec")
    persona_dni = request.session.get("persona_dni")

    return render(request, "ventas/form2.html", {
        "evn":           evn,
        "evento_desc":   svc.get_evento(evn),
        "nombre":        request.session.get("nombre", ""),
        "img_evento":    svc.get_imagen_evento(evn),
        "img_sponsor":   svc.get_imagen_sponsor(evn),
        "precios_lista": precios_lista,
        "fechas":        fechas,
        "publicaciones": svc.get_publicaciones(evn),
        "cupon_sec":     str(cupon_sec).zfill(6) if cupon_sec else "",
        "persona_dni":   str(persona_dni) if persona_dni else "",
    })


def sorteos_fecha(request, evn, fecha):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)

    sorteos = svc.get_sorteos_de_fecha(evn, fecha)
    return render(request, "ventas/form3.html", {
        "evn":        evn,
        "fecha_fmt":  svc.fmt_fecha(fecha),
        "sorteos":    sorteos,
        "img_evento": svc.get_imagen_evento(evn),
    })


def ayuda(request, evn, codi):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)

    titulos = {"SOMOS": "Quiénes Somos", "HELP1": "Ayuda"}
    textos  = svc.get_textos_ayuda(codi)
    return render(request, "ventas/ayuda.html", {
        "evn":    evn,
        "titulo": titulos.get(codi, codi),
        "textos": textos,
    })


def logout_view(request, evn):
    request.session.flush()
    return redirect("ventas:login", evn=evn)


def seleccionar_view(request, evn):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)
    pvt = svc.get_pvt_sort(evn)
    cantidades = []
    if pvt:
        cantidades = sorted(i for i in pvt["precios"] if i in pvt["rangos"])

    cupon_sec    = request.session.get("cupon_sec")
    nums_pref    = request.session.get("sel_nums_pref") or []
    sel_cantidad = request.session.get("sel_cantidad") or ""
    usuario      = request.session.get("usuario", "")
    tope_info    = svc.check_tope_ventas(evn, usuario)

    return render(request, "ventas/seleccionar.html", {
        "evn":           evn,
        "img_evento":    svc.get_imagen_evento(evn),
        "cantidades":    cantidades,
        "cupon_sec":     cupon_sec,
        "sel_cantidad":  sel_cantidad,
        "sel_nums_pref": nums_pref,
        "tope_info":     tope_info,
    })


@csrf_exempt
def proximo_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    try:
        cantidad = int(body.get("cantidad", 0))
    except Exception:
        return JsonResponse({"ok": False, "error": "Cantidad inválida"})
    nums_pref = body.get("nums_pref") or []

    request.session["sel_cantidad"]  = cantidad
    request.session["sel_nums_pref"] = nums_pref

    usuario   = request.session.get("usuario", "")
    tope_info = svc.check_tope_ventas(evn, usuario)
    if tope_info['bloqueado']:
        return JsonResponse({
            "ok": False,
            "tope_superado": True,
            "error": (
                f"Tiene {tope_info['count']} ventas sin rendir "
                f"(tope: {tope_info['tope']}). Debe rendir antes de continuar."
            ),
        })

    pvt = svc.get_pvt_sort(evn)
    if not pvt or cantidad not in pvt.get("rangos", {}):
        return JsonResponse({"ok": False, "error": "Cantidad no configurada"})

    rango = pvt["rangos"][cantidad]
    secuencias = svc.get_secuencias_disponibles(evn, rango["scd"], rango["sch"], nums_pref or None)
    if not secuencias:
        return JsonResponse({"ok": False, "error": "No hay cupones disponibles"})

    cartones = svc.get_cartones_cupon(evn, secuencias[0])
    return JsonResponse({"ok": True, "secuencias": secuencias, "sec": secuencias[0], "cartones": cartones})


@csrf_exempt
def cartones_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        body = json.loads(request.body)
        sec = int(body.get("sec", 0))
    except Exception:
        return JsonResponse({"ok": False, "error": "Datos inválidos"}, status=400)
    if not sec:
        return JsonResponse({"ok": False, "error": "Secuencia inválida"})
    cartones = svc.get_cartones_cupon(evn, sec)
    return JsonResponse({"ok": True, "sec": sec, "cartones": cartones})


def movimientos_view(request, evn, prd):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)

    from datetime import date, timedelta
    hoy  = date.today()
    ayer = hoy - timedelta(days=1)

    desde_str = request.GET.get('desde', ayer.strftime('%Y-%m-%d'))
    hasta_str = request.GET.get('hasta', hoy.strftime('%Y-%m-%d'))
    fpgo_filt = request.GET.get('fpgo', '')
    estd_filt = request.GET.get('estd', '')
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except Exception:
        page = 1

    try:
        desde_date = date.fromisoformat(desde_str)
    except Exception:
        desde_date = ayer
    try:
        hasta_date = date.fromisoformat(hasta_str)
    except Exception:
        hasta_date = hoy

    usuario  = request.session.get("usuario", "")
    movs_raw, total = svc.get_movimientos(
        evn, usuario, prd,
        desde=desde_date, hasta=hasta_date,
        fpgo=fpgo_filt or None,
        estd=estd_filt or None,
        page=page,
    )
    movimientos = [
        {**m, 'valo_fmt': _fmt_precio(m['valo'])}
        for m in movs_raw
    ]
    total_pages = max(1, (total + svc.PAGE_SIZE - 1) // svc.PAGE_SIZE)
    page = min(page, total_pages)
    _prd_fallback = {1: 'Ventas', 2: 'Rendiciones', 3: 'Comisiones'}
    prd_desc = svc.get_prd_desc(prd) or _prd_fallback.get(prd, str(prd))
    return render(request, "ventas/movimientos.html", {
        "prd":         prd,
        "evn":         evn,
        "img_evento":  svc.get_imagen_evento(evn),
        "prd_desc":    prd_desc,
        "movimientos": movimientos,
        "desde":       desde_date.strftime('%Y-%m-%d'),
        "hasta":       hasta_date.strftime('%Y-%m-%d'),
        "fpgo_filt":   fpgo_filt,
        "estd_filt":   estd_filt,
        "page":        page,
        "total_pages": total_pages,
        "total":       total,
        "fpgo_opts":   [('','Todos'),('E','Efectivo'),('T','Transf.'),
                        ('C','T.Crd.'),('D','T.Déb.'),('Q','QR'),('blank','S/Pago')],
        "estd_opts":   [('','Todos'),('I','Ingresada'),('X','En proceso'),('R','Rendida')],
    })


# ================================================================ ADMIN
def adm_login_view(request, evn):
    info = svc.get_evento(evn)
    return render(request, "ventas/adm_login.html", {
        "evn":         evn,
        "evento_desc": info['evento'],
        "img_evento":  svc.get_imagen_evento(evn),
    })


@csrf_exempt
def adm_login_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)
    usuario = str(body.get("usuario", "")).strip()
    pwd     = str(body.get("pwd", "")).strip()
    if not usuario or not pwd:
        return JsonResponse({"ok": False, "error": "Datos incompletos"})
    ok, nombre, error = svc.validate_admin_user(evn, usuario, pwd)
    if not ok:
        return JsonResponse({"ok": False, "error": error})
    request.session["adm_evn"]     = evn
    request.session["adm_usuario"] = usuario
    request.session["adm_nombre"]  = nombre
    return JsonResponse({"ok": True, "nombre": nombre})


def adm_principal_view(request, evn):
    if request.session.get("adm_evn") != evn:
        return redirect("ventas:adm_login", evn=evn)

    from datetime import date, timedelta
    hoy  = date.today()
    ayer = hoy - timedelta(days=1)

    desde_str = request.GET.get('desde', ayer.strftime('%Y-%m-%d'))
    hasta_str = request.GET.get('hasta', hoy.strftime('%Y-%m-%d'))
    try:
        desde_date = date.fromisoformat(desde_str)
    except Exception:
        desde_date = ayer
    try:
        hasta_date = date.fromisoformat(hasta_str)
    except Exception:
        hasta_date = hoy

    rendiciones_raw = svc.get_rendiciones_admin(evn, desde=desde_date, hasta=hasta_date)
    rendiciones = [{**r, 'valo_fmt': _fmt_precio(r['valo'])} for r in rendiciones_raw]

    return render(request, "ventas/adm_principal.html", {
        "evn":         evn,
        "evento_desc": svc.get_evento(evn),
        "img_evento":  svc.get_imagen_evento(evn),
        "nombre":      request.session.get("adm_nombre", ""),
        "desde":       desde_date.strftime('%Y-%m-%d'),
        "hasta":       hasta_date.strftime('%Y-%m-%d'),
        "rendiciones": rendiciones,
    })


def adm_mensajes_view(request, evn):
    if request.session.get("adm_evn") != evn:
        return redirect("ventas:adm_login", evn=evn)
    import logging
    log = logging.getLogger(__name__)
    fil_fecha = request.GET.get('fecha', '').strip()
    fil_idpr  = request.GET.get('idpr',  '').strip()
    fil_mrka  = request.GET.get('mrka',  '').strip()
    error_db  = ''
    try:
        idpr_opciones = svc.get_msg_idpr_opciones(evn)
        mensajes      = svc.get_msg_proc(evn,
                            fecha=fil_fecha or None,
                            idpr=fil_idpr   or None,
                            mrka=fil_mrka   or None)
    except Exception as e:
        log.error("adm_mensajes error: %s", e, exc_info=True)
        mensajes      = []
        idpr_opciones = []
        error_db      = str(e)
    return render(request, 'ventas/adm_mensajes.html', {
        'evn':           evn,
        'evento_desc':   svc.get_evento(evn)['evento'],
        'img_evento':    svc.get_imagen_evento(evn),
        'nombre':        request.session.get('adm_nombre', ''),
        'mensajes':      mensajes,
        'idpr_opciones': idpr_opciones,
        'fil_fecha':     fil_fecha,
        'fil_idpr':      fil_idpr,
        'fil_mrka':      fil_mrka,
        'error_db':      error_db,
    })


@csrf_exempt
def adm_reenviar_api(request, evn):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    if request.session.get('adm_evn') != evn:
        return JsonResponse({'ok': False, 'error': 'Sesión inválida'})
    try:
        body   = json.loads(request.body)
        msg_id = int(body.get('msg_id', 0))
        via    = str(body.get('via', 'M')).strip()
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'})
    if not msg_id or via not in ('M', 'W', 'T'):
        return JsonResponse({'ok': False, 'error': 'Parámetros inválidos'})
    ok, msg = svc.reenviar_msg_proc(evn, msg_id, via)
    return JsonResponse({'ok': ok, 'msg': msg})


@csrf_exempt
def adm_preview_plantilla_api(request, evn):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    if request.session.get('adm_evn') != evn:
        return JsonResponse({'ok': False, 'error': 'Sesión inválida'})
    try:
        body   = json.loads(request.body)
        msg_id = int(body.get('msg_id', 0))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'})
    data = svc.get_preview_plantilla(evn, msg_id)
    if data is None:
        return JsonResponse({'ok': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'ok': True, **data})


def adm_logout_view(request, evn):
    for key in ("adm_evn", "adm_usuario", "adm_nombre"):
        request.session.pop(key, None)
    return redirect("ventas:adm_login", evn=evn)




@csrf_exempt
def adm_certificar_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("adm_evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"})
    usuario_vend = str(body.get("usuario_vend", "")).strip()
    nro_rend     = str(body.get("nro_rend", "")).strip()
    ref_banco    = str(body.get("ref_banco", "")).strip()
    if not usuario_vend or not nro_rend or not ref_banco:
        return JsonResponse({"ok": False, "error": "Complete los tres campos"})
    ok, msg = svc.certificar_rendicion(evn, usuario_vend, nro_rend, ref_banco)
    return JsonResponse({"ok": ok, "error": msg if not ok else ""})


# ================================================================ FIN ADMIN
def rendicion_view(request, evn):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)

    from datetime import date
    usuario   = request.session.get("usuario", "")
    nombre    = request.session.get("nombre", "")
    desde_str = request.GET.get('desde', '')
    hasta_str = request.GET.get('hasta', '')
    fpgo_filt = request.GET.get('fpgo', '')

    desde_date = hasta_date = None
    try:
        if desde_str:
            desde_date = date.fromisoformat(desde_str)
        if hasta_str:
            hasta_date = date.fromisoformat(hasta_str)
    except Exception:
        pass

    data = svc.get_rendicion_data(
        evn, usuario,
        desde=desde_date, hasta=hasta_date,
        fpgo=fpgo_filt or None,
    )
    for v in data['ventas']:
        v['valo_fmt'] = _fmt_precio(v['valo'])

    fpgo_labels = {
        'E': 'Efectivo', 'T': 'Transferencia', 'C': 'T. Crédito',
        'D': 'T. Débito', 'Q': 'QR', 'blank': 'Sin pago', '': 'Todos',
    }
    return render(request, "ventas/rendicion.html", {
        "evn":          evn,
        "evento_desc":  svc.get_evento(evn),
        "usuario":      usuario,
        "nombre":       nombre,
        "desde":        desde_str,
        "hasta":        hasta_str,
        "fpgo_filt":    fpgo_filt,
        "fpgo_label":   fpgo_labels.get(fpgo_filt, fpgo_filt),
        "ventas":       data['ventas'],
        "total_fmt":    _fmt_precio(data['total']),
        "pcjcom":       data['pcjcom'],
        "comision_fmt": _fmt_precio(data['comision']),
        "neto_fmt":     _fmt_precio(data['neto']),
        "nro_rend_fmt": data['nro_rend_fmt'],
        "hay_ventas":   len(data['ventas']) > 0,
    })


@csrf_exempt
def rendicion_confirmar_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"})

    from datetime import date
    usuario   = request.session.get("usuario", "")
    desde_str = body.get('desde', '')
    hasta_str = body.get('hasta', '')
    fpgo      = body.get('fpgo', '')

    desde_date = hasta_date = None
    try:
        if desde_str:
            desde_date = date.fromisoformat(desde_str)
        if hasta_str:
            hasta_date = date.fromisoformat(hasta_str)
    except Exception:
        pass

    nro = svc.confirmar_rendicion(
        evn, usuario,
        desde=desde_date, hasta=hasta_date,
        fpgo=fpgo or None,
    )
    if nro is None:
        return JsonResponse({"ok": False, "error": "Sin ventas para rendir con el filtro aplicado"})
    return JsonResponse({"ok": True, "nro_rend": nro})


# ================================================================ QR AUTO-ASIGNACION
def qr_view(request, evn):
    return render(request, 'ventas/qr.html', {
        'evn':         evn,
        'evento_desc': svc.get_evento(evn),
        'img_evento':  svc.get_imagen_evento(evn),
        'msg_qr':      svc.get_evento_msgqr(evn).replace('\\n', '\n'),
        'bloqueo_msg': svc.check_qr_habilitado(evn),
    })


@csrf_exempt
def qr_buscar_api(request, evn):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    try:
        body = json.loads(request.body)
        nid  = int(body.get('nid', 0))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'DNI inválido'})
    if not nid:
        return JsonResponse({'ok': False, 'error': 'Ingrese el DNI'})
    persona = svc.get_persona(nid)
    if persona:
        return JsonResponse({
            'ok':       True,
            'found':    True,
            'nombre':   persona.get('per_nombre', ''),
            'fecha_nac': persona.get('per_fecha_nac', ''),
            'celular':  persona.get('per_celular', ''),
        })
    return JsonResponse({'ok': True, 'found': False})


@csrf_exempt
def qr_asignar_api(request, evn):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    try:
        body = json.loads(request.body)
        nid  = int(body.get('nid', 0))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'DNI inválido'})
    if not nid:
        return JsonResponse({'ok': False, 'error': 'DNI requerido'})

    nombre    = str(body.get('nombre', '')).strip()
    fecha_nac = str(body.get('fecha_nac', '')).strip() or None
    celular   = str(body.get('celular', '')).strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre es requerido'})

    import logging, traceback
    log = logging.getLogger(__name__)
    try:
        sec, cartones, cantidad, error = svc.asignar_cupon_qr(evn, nid, nombre, fecha_nac, celular)
    except Exception as exc:
        log.error("qr_asignar_api excepcion: %s\n%s", exc, traceback.format_exc())
        return JsonResponse({'ok': False, 'error': f'Error interno: {exc}'})
    if error:
        return JsonResponse({'ok': False, 'error': error})
    return JsonResponse({
        'ok':       True,
        'sec':      str(sec).zfill(6),
        'cantidad': cantidad,
        'cartones': cartones,
    })


def qr_flyer_view(request, evn):
    import base64, io, qrcode
    url_qr = request.build_absolute_uri(f'/{evn}/qr/')
    qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=2)
    qr.add_data(url_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1565c0", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return render(request, 'ventas/qr_flyer.html', {
        'evn':         evn,
        'evento_desc': svc.get_evento(evn),
        'img_evento':  svc.get_imagen_evento(evn),
        'msg_qr':      svc.get_evento_msgqr(evn).replace('\\n', '\n'),
        'url_qr':      url_qr,
        'qr_b64':      qr_b64,
    })


# ================================================================ FIN QR
def datos_view(request, evn):
    if request.session.get("evn") != evn:
        return redirect("ventas:login", evn=evn)
    return render(request, "ventas/datos.html", {
        "evn":             evn,
        "img_evento":      svc.get_imagen_evento(evn),
        "tipos_identidad": svc.get_all_tipoidentidad(),
        "tipos_persona":   svc.get_all_tipopersona(),
        "persona_dni":     str(request.session.get("persona_dni", "") or ""),
    })


@csrf_exempt
def datos_buscar_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        body = json.loads(request.body)
        dni = int(body.get("dni", 0))
    except Exception:
        return JsonResponse({"ok": False, "error": "DNI inválido"})
    if not dni:
        return JsonResponse({"ok": False, "error": "Ingrese el DNI"})
    persona = svc.get_persona(dni)
    if persona:
        persona['_loc_desc'] = svc.get_nombre_by_id('app_core_localidad', 'loc_nombre', persona.get('per_localidad_id'))
        persona['_prv_desc'] = svc.get_nombre_by_id('app_core_provincia', 'pro_provincia', persona.get('per_provincia_id'))
        persona['_tid_desc'] = svc.get_nombre_by_id('app_gbl_tipoidentidad','tid_tipo_identidad',persona.get('per_tipo_identidad_id'))
        persona['_tpe_desc'] = svc.get_nombre_by_id('app_gbl_tipopersona', 'tpe_tipo_persona',  persona.get('per_tipo_persona_id'))
        return JsonResponse({"ok": True, "found": True, "persona": persona})
    defaults = svc.get_evento_defaults(evn)
    return JsonResponse({"ok": True, "found": False,
                         "persona": {"per_numero_identidad": str(dni)},
                         "defaults": defaults})


@csrf_exempt
def datos_guardar_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "error": "Datos inválidos"})

    dni = data.get('per_numero_identidad')

    if data.get('found'):
        request.session['persona_dni'] = int(dni) if dni else None
        return JsonResponse({"ok": True})

    if not data.get('per_nombre'):
        return JsonResponse({"ok": False, "error": "Nombre es requerido"})
    if not data.get('per_calle'):
        return JsonResponse({"ok": False, "error": "Calle es requerida"})
    if not data.get('per_localidad_id'):
        return JsonResponse({"ok": False, "error": "Localidad es requerida"})
    if not data.get('per_provincia_id'):
        return JsonResponse({"ok": False, "error": "Provincia es requerida"})
    if not data.get('per_celular') and not data.get('per_email'):
        return JsonResponse({"ok": False, "error": "Celular o eMail son requeridos"})
    if not data.get('per_tipo_identidad_id'):
        return JsonResponse({"ok": False, "error": "Tipo de identidad es requerido"})
    if not data.get('per_tipo_persona_id'):
        return JsonResponse({"ok": False, "error": "Tipo de persona es requerido"})
    if not data.get('per_fecha_nac'):
        return JsonResponse({"ok": False, "error": "Fecha de nacimiento es requerida"})

    try:
        svc.save_persona(data)
        request.session['persona_dni'] = int(dni) if dni else None
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


@csrf_exempt
def confirmar_venta_api(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})

    cupon_sec   = request.session.get("cupon_sec")
    persona_dni = request.session.get("persona_dni")

    if not cupon_sec:
        return JsonResponse({"ok": False, "error": "Falta seleccionar el cupón"})
    if not persona_dni:
        return JsonResponse({"ok": False, "error": "Falta ingresar los datos del comprador"})

    try:
        body = json.loads(request.body) if request.body else {}
    except Exception:
        body = {}
    fpgo = str(body.get('fpgo', '') or '').strip()
    if fpgo not in ('E', 'T', 'C', 'D', 'Q'):
        return JsonResponse({"ok": False, "error": "Seleccione la forma de pago"})

    try:
        persona = svc.get_persona(persona_dni)
        if not persona:
            return JsonResponse({"ok": False, "error": "No se encontraron los datos del comprador"})

        loc_text = svc.get_nombre_by_id('app_core_localidad', 'loc_nombre', persona.get('per_localidad_id'))
        prv_text = svc.get_nombre_by_id('app_core_provincia', 'pro_provincia', persona.get('per_provincia_id'))

        def v(key): return persona.get(key) or ''
        dom = f"{v('per_barrio')}|{v('per_calle')}|{v('per_puerta')}|{v('per_piso')}|{v('per_depto')}|"
        loc = f"{prv_text}|{loc_text}|{v('per_codigo_postal')}|"
        ref = f"{v('per_celular')}|{v('per_email')}|{v('per_telefono')}|{v('per_alias_cbu')}|{v('per_cbu')}|"

        pvt = svc.get_pvt_sort(evn)
        try:
            sel_cantidad = int(request.session.get("sel_cantidad") or 0)
        except Exception:
            sel_cantidad = 0
        precio = pvt["precios"].get(sel_cantidad, 0) if pvt else 0

        usuario = request.session.get("usuario", "")
        ok = svc.vender_cupon(
            evn, int(cupon_sec), usuario,
            nid=int(persona_dni), nom=v('per_nombre'),
            dom=dom, loc=loc, ref=ref, fpgo=fpgo, precio=precio
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error interno: {e}"})

    if not ok:
        return JsonResponse({"ok": False, "error": "No se pudo confirmar la venta. El cupón ya no está disponible."})

    for key in ("cupon_sec", "persona_dni", "sel_cantidad", "sel_nums_pref"):
        request.session.pop(key, None)

    svc.enviar_notif_venta(evn, int(cupon_sec), persona, pvt or {})

    return JsonResponse({"ok": True})


def datos_lookup_api(request, evn):
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    tipo = request.GET.get("tipo", "")
    q    = request.GET.get("q", "").strip()
    prov = request.GET.get("prov", "").strip()

    if tipo == "tipoidentidad":
        return JsonResponse({"ok": True, "items": svc.get_all_tipoidentidad()})
    elif tipo == "tipopersona":
        return JsonResponse({"ok": True, "items": svc.get_all_tipopersona()})
    elif tipo == "provincia":
        if len(q) < 2:
            return JsonResponse({"ok": True, "items": []})
        return JsonResponse({"ok": True, "items": svc.get_lookup_provincia(q)})
    elif tipo == "localidad":
        if len(q) < 2:
            return JsonResponse({"ok": True, "items": []})
        return JsonResponse({"ok": True, "items": svc.get_lookup_localidad(q, prov or None)})
    return JsonResponse({"ok": False, "error": "Tipo inválido"})


@csrf_exempt
def confirmar_cupon(request, evn):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if request.session.get("evn") != evn:
        return JsonResponse({"ok": False, "error": "Sesión inválida"})
    try:
        body = json.loads(request.body)
        sec = int(body.get("sec", 0))
    except Exception:
        return JsonResponse({"ok": False, "error": "Datos inválidos"}, status=400)
    if not sec:
        return JsonResponse({"ok": False, "error": "Cupón inválido"})
    usuario = request.session.get("usuario", "")
    ok = svc.reservar_cupon(evn, sec, usuario)
    if not ok:
        return JsonResponse({"ok": False, "concurrencia": True,
                             "error": "Debe buscar nuevamente por una concurrencia operativa"})
    request.session["cupon_sec"] = str(sec)
    return JsonResponse({"ok": True})
