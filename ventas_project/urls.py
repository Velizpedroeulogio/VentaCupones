from django.urls import include, path

urlpatterns = [
    path("", include("ventas.urls")),
]
