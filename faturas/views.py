from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Compra, Fatura
from faturas.forms import CompraForm



def home(request):
    return render(request, 'faturas/index.html')

@login_required
def cadastrar_compra(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.usuario = request.user
            compra.save()
            return redirect('faturas:lista_compras')
    else:
        form = CompraForm()

    return render(request, 'faturas/cadastrar_compra.html', {'form': form})


@login_required
def lista_compras(request):
    compras = Compra.objects.filter(usuario=request.user)
    return render(request, 'faturas/lista_compras.html', {'compras': compras})


@login_required
def ver_fatura(request, mes, ano):
    fatura, created = Fatura.objects.get_or_create(usuario=request.user, mes=mes, ano=ano)
    fatura.calcular_total()
    return render(request, 'faturas/ver_fatura.html', {'fatura': fatura})

@login_required
def deletar_compra(request, id):
    compra = Compra.objects.get(id=id)
    if request.method == 'POST':
        compra.delete()
        return redirect('faturas:lista_compras')
    return render(request, 'faturas/deletar_compra.html', {'compra': compra})

