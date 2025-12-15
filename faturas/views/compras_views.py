from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from faturas.models import Compra
from django.contrib.auth.models import User
from faturas.forms import CompraForm
from faturas.service.compras_service import *
from faturas.service.usuario_service import *
from datetime import datetime
from documentos.models import UserFile, UserActivity
from faturas.service.fatura_service import gera_fatura
from django.core.paginator import Paginator


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'faturas/home.html')
    
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year

    faturas, total_mes, _ = gera_fatura(request, mes_atual, ano_atual)

    total_documentos = UserFile.objects.filter(
        usuario=request.user
    ).count()

    ultimas_atividades = UserActivity.objects.filter(
        usuario=request.user
    ).order_by('-data')[:5]

    atividades_formatadas = []
    for atividade in ultimas_atividades:
        atividades_formatadas.append({
            'descricao': atividade.descricao,
            'data': atividade.data,
            'tipo': 'compra' if atividade.tipo == 'compra' else 'arquivo'
        })

    context = {
        'total_mes': total_mes,
        'total_documentos': total_documentos,
        'ultimas_atividades': atividades_formatadas
    }

    return render(request, 'faturas/home.html', context)


@login_required
def cadastrar_compra(request):
    if request.method == 'POST':
        import pprint
        pprint.pprint(request.POST)
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.usuario = request.user
            falha = validar_compra(compra)
            if falha is None:
                salvar_compra(compra)
            else:
                form.add_error(falha[0], falha[1])
        return render(request, 'faturas/cadastrar_compra.html', {'form': form})

    else:
        form = CompraForm()

    return render(request, 'faturas/cadastrar_compra.html', {'form': form})


@login_required
def deletar_compra(request, id):
    compra = Compra.objects.get(id=id)
    if request.method == 'POST':
        compra.delete()
        return redirect('faturas:lista_compras')

@login_required
def ver_compras(request):
    compras_qs = Compra.objects.filter(usuario=request.user).order_by('-data_compra')
    paginator = Paginator(compras_qs, 20)  # 20 compras por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for compra in page_obj:
        if not compra.compra_parcelada:
            compra.parcelas = ''

    context = {
        'compras': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    }

    return render(request, 'faturas/tables.html', context)

@staff_member_required
def cadastrar_compra_admin(request):
    usuarios = User.objects.all()
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.usuario = User.objects.get(id=request.POST.get('usuario'))
            falha = validar_compra(compra)
            if falha is None:
                salvar_compra(compra)
            else:
                form.add_error(falha[0], falha[1])
        return render(request, 'faturas/cadastro_compras_admin.html', {'form': form, 'usuarios': usuarios})

    else:
        form = CompraForm()

    return render(request, 'faturas/cadastro_compras_admin.html', {'form': form, 'usuarios': usuarios})

    
def registrar_usuario(request):
    registro = registra_usuario(request)
    if registro is None:
        redirect('login')
    
    return render(registro, 'registration/register.html')

