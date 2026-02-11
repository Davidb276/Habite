from django.shortcuts import render

from django.shortcuts import render
from .models import Producto

def catalogo(request):
    productos = Producto.objects.all()
    return render(request, "catalogo.html", {"productos": productos})
