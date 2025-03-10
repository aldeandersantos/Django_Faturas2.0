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
    compras = Compra.objects.filter(usuario=request.user)
    for compra in compras:
        if not compra.compra_parcelada:
            compra.parcelas = ''
    return render(request, 'faturas/tables.html', {'compras': compras})

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

