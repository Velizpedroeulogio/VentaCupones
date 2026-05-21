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
    prd_desc = svc.get_prd_desc(prd) or ('Ventas' if prd == 1 else 'Comisiones')
    return render(request, "ventas/movimientos.html", {
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
        "estd_opts":   [('','Todos'),('I','Ingresada'),('R','Rendida')],
    })


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
