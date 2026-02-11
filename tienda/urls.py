from django.urls import path
from .views import catalogo

urlpatterns = [
    path("", catalogo, name="catalogo"),
]
