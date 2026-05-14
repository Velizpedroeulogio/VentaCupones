import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from . import services as svc


def login_view(request, evn):
    evento_desc = svc.get_evento(evn)
    img_evento  = svc.get_imagen_evento(evn)
    return render(request, "ventas/form1.html", {
        "evn":         evn,
        "evento_desc": evento_desc,
        "img_evento":  img_evento,
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

    usuario = request.session.get("usuario", "")
    nombre  = request.session.get("nombre", "")

    pvt = svc.get_pvt_sort(evn)
    fechas  = []
    precios = {}
    fchd_fmt = fchh_fmt = ""

    if pvt:
        precios  = pvt["precios"]
        fchd_fmt = svc.fmt_fecha(pvt["pvt_fchd"])
        fchh_fmt = svc.fmt_fecha(pvt["pvt_fchh"])
        fechas   = svc.get_fechas_sorteo(evn, pvt["pvt_fchd"], pvt["pvt_fchh"])

    publicaciones = svc.get_publicaciones(evn)
    img_evento    = svc.get_imagen_evento(evn)
    img_sponsor   = svc.get_imagen_sponsor(evn)
    evento_desc   = svc.get_evento(evn)

    precios_lista = [
        {"chns": n, "precio": p}
        for n, p in sorted(precios.items())
    ]

    return render(request, "ventas/form2.html", {
        "evn":          evn,
        "evento_desc":  evento_desc,
        "usuario":      usuario,
        "nombre":       nombre,
        "img_evento":   img_evento,
        "img_sponsor":  img_sponsor,
        "fchd_fmt":     fchd_fmt,
        "fchh_fmt":     fchh_fmt,
        "precios_lista": precios_lista,
        "fechas":       fechas,
        "publicaciones": publicaciones,
    })


def logout_view(request, evn):
    request.session.flush()
    return redirect("ventas:login", evn=evn)
