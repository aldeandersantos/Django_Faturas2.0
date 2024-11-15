from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Compra
from faturas.forms import CompraForm
from faturas.service import *
from faturas.utils import mes_ano_atual



def home(request):
    return render(request, 'faturas/home.html')


@login_required
def cadastrar_compra(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.usuario = request.user
            falha = validar_compra(compra)
            if falha is None:
                compra.save()
                if compra.compra_parcelada:
                    parcelar_compra(compra)
            else:
                form.add_error(falha[0], falha[1])
        return render(request, 'faturas/cadastrar_compra.html', {'form': form})

    else:
        form = CompraForm()

    return render(request, 'faturas/cadastrar_compra.html', {'form': form})


@login_required
def ver_fatura(request):
    mes, ano = mes_ano_atual()
    fatura, total = gera_fatura(request, mes, ano)
    return render(request, 'faturas/ver_fatura.html', {'fatura': fatura, 'mes': mes, 'ano': ano, 'total': total})

@login_required
def deletar_compra(request, id):
    compra = Compra.objects.get(id=id)
    if request.method == 'POST':
        compra.delete()
    return redirect('faturas:lista_compras')

@login_required
def ver_compras(request):
    compras = Compra.objects.filter(usuario=request.user)
    for compra in compras:
        if not compra.compra_parcelada:
            compra.parcelas = ''
    return render(request, 'faturas/tables.html', {'compras': compras})

