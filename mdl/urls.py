from django.urls import path
from . import views

app_name = "mdl"

urlpatterns = [
    path("",          views.tablas,   name="tablas"),
    path("columnas/", views.columnas, name="columnas"),
    path("indices/",  views.indices,  name="indices"),
]
