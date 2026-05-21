from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("<int:evn>/",                    views.login_view,    name="login"),
    path("<int:evn>/login/",              views.login_api,     name="login_api"),
    path("<int:evn>/principal/",          views.principal,     name="principal"),
    path("<int:evn>/logout/",             views.logout_view,   name="logout"),
    path("<int:evn>/sorteos/<int:fecha>/", views.sorteos_fecha, name="sorteos"),
    path("<int:evn>/ayuda/<str:codi>/",    views.ayuda,          name="ayuda"),
    path("<int:evn>/seleccionar/",         views.seleccionar_view, name="seleccionar"),
    path("<int:evn>/seleccionar/proximo/", views.proximo_api,    name="proximo_api"),
    path("<int:evn>/seleccionar/confirmar/", views.confirmar_cupon, name="confirmar_cupon"),
    path("<int:evn>/seleccionar/cartones/",  views.cartones_api,    name="cartones_api"),
    path("<int:evn>/datos/",                 views.datos_view,       name="datos"),
    path("<int:evn>/datos/buscar/",          views.datos_buscar_api,  name="datos_buscar"),
    path("<int:evn>/datos/guardar/",         views.datos_guardar_api, name="datos_guardar"),
    path("<int:evn>/datos/lookup/",          views.datos_lookup_api,  name="datos_lookup"),
    path("<int:evn>/confirmar-venta/",       views.confirmar_venta_api, name="confirmar_venta"),
    path("<int:evn>/movimientos/<int:prd>/", views.movimientos_view,    name="movimientos"),
    path("<int:evn>/adm/",                   views.adm_login_view,       name="adm_login"),
    path("<int:evn>/adm/login/",             views.adm_login_api,        name="adm_login_api"),
    path("<int:evn>/adm/principal/",         views.adm_principal_view,   name="adm_principal"),
    path("<int:evn>/adm/logout/",            views.adm_logout_view,      name="adm_logout"),
    path("<int:evn>/adm/certificar/",        views.adm_certificar_api,   name="adm_certificar"),
    path("<int:evn>/rendicion/",             views.rendicion_view,        name="rendicion"),
    path("<int:evn>/rendicion/confirmar/",   views.rendicion_confirmar_api, name="rendicion_confirmar"),
    path("<int:evn>/qr/",                    views.qr_view,               name="qr"),
    path("<int:evn>/qr/buscar/",             views.qr_buscar_api,         name="qr_buscar"),
    path("<int:evn>/qr/asignar/",            views.qr_asignar_api,        name="qr_asignar"),
]
