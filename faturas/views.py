import pandas as pd

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Compra
from django.http import HttpResponse
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
                salvar_compra(compra)
            else:
                form.add_error(falha[0], falha[1])
        return render(request, 'faturas/cadastrar_compra.html', {'form': form})

    else:
        form = CompraForm()

    return render(request, 'faturas/cadastrar_compra.html', {'form': form})


@login_required
def ver_fatura(request):
    mes = request.GET.get('mes', None)
    ano = request.GET.get('ano', None)
    if mes is None or ano is None:
        mes, ano = mes_ano_atual()
    faturas, total = gera_fatura(request, mes, ano)
    return render(request, 'faturas/ver_fatura.html', {'faturas': faturas, 'mes': mes, 'ano': ano, 'total': total})

@login_required
def deletar_compra(request, id):
    compra = Compra.objects.get(id=id)
    compras = Fatura.objects.filter(compra=compra)
    if request.method == 'POST':
        compra.delete()
        compras.delete()
        return redirect('faturas:lista_compras')

@login_required
def ver_compras(request):
    compras = Compra.objects.filter(usuario=request.user)
    for compra in compras:
        if not compra.compra_parcelada:
            compra.parcelas = ''
    return render(request, 'faturas/tables.html', {'compras': compras})

@staff_member_required
def exportar_fatura_excel(request):
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    try:
        if mes is None or ano is None:
            mes, ano = mes_ano_atual()
        
        faturas, total = gera_fatura(request, mes, ano)
        
        data = []
        for fatura in faturas:
            data.append({
                'Nome da Compra': fatura.nome_compra,
                'Valor': f'R$ {fatura.valor_compra:.2f}',
                'Data da compra': fatura.data_compra.strftime('%d/%m/%Y'),
                'Parcela atual': fatura.parcela_atual,
            })
        
        if not data:
            return HttpResponse("Nenhuma fatura encontrada para exportar.", status=404)
        
        df = pd.DataFrame(data)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=fatura_{mes}_{ano}.xlsx'
        
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Faturas')
        
        return response
    
    except Exception as e:
        return HttpResponse(f"Erro ao gerar o arquivo Excel: {str(e)}", status=500)

