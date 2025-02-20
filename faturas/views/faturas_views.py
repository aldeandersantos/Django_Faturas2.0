import openpyxl
import pandas as pd
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from faturas.utils import mes_ano_atual
from faturas.service.compras_service import *
from faturas.service.fatura_service import *
from django.shortcuts import render
from faturas.views.compras_views import *



@login_required
def ver_fatura(request):
    mes = request.GET.get('mes', None)
    ano = request.GET.get('ano', None)
    
    if mes is None or ano is None:
        mes, ano = mes_ano_atual()
    else:
        mes = int(mes)
        ano = int(ano)
        
    faturas, total, compras = gera_fatura(request, mes, ano)
    
    context = {
        'faturas': faturas,
        'mes': str(mes),
        'ano': ano,
        'total': total,
        'compras': compras
    }
    
    return render(request, 'faturas/ver_fatura.html', context)


@login_required
def importa_xlsx(request):
    usuarios = User.objects.all()
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        # Abre o arquivo XLSX
        workbook = openpyxl.load_workbook(uploaded_file)
        sheet = workbook.active

        # Processa os dados para criar uma lista de dicionários
        data = []
        headers = [cell.value for cell in sheet[1]]  # Pega os cabeçalhos da primeira linha
        for row in sheet.iter_rows(min_row=2, values_only=True):  # Ignora a primeira linha
            row_data = {headers[i]: value for i, value in enumerate(row)}
            # Ignora a linha se todos os valores forem None
            if all(value is None for value in row_data.values()):
                break
            data.append(row_data)
            
        dados = tratar_import_fatura(request, data)
        return render(request, 'faturas/importar_xlsx.html', {'dados': dados, 'usuarios': usuarios})

    return render(request, 'faturas/importar_xlsx.html', {'usuarios': usuarios})


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