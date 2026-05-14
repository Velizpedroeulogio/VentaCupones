from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("<int:evn>/",                    views.login_view,    name="login"),
    path("<int:evn>/login/",              views.login_api,     name="login_api"),
    path("<int:evn>/principal/",          views.principal,     name="principal"),
    path("<int:evn>/logout/",             views.logout_view,   name="logout"),
    path("<int:evn>/sorteos/<int:fecha>/", views.sorteos_fecha, name="sorteos"),
    path("<int:evn>/ayuda/<str:codi>/",   views.ayuda,         name="ayuda"),
]
