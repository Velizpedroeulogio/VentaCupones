from django.urls import include, path

urlpatterns = [
    path("",     include("ventas.urls")),
    path("mdl/", include("mdl.urls")),
]
