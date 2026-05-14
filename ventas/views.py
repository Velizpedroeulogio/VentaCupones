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

    return render(request, "ventas/form2.html", {
        "evn":           evn,
        "evento_desc":   svc.get_evento(evn),
        "nombre":        request.session.get("nombre", ""),
        "img_evento":    svc.get_imagen_evento(evn),
        "img_sponsor":   svc.get_imagen_sponsor(evn),
        "precios_lista": precios_lista,
        "fechas":        fechas,
        "publicaciones": svc.get_publicaciones(evn),
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
