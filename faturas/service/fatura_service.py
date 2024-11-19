from decimal import Decimal
from faturas.forms import CompraForm
from faturas.models import Compra, Fatura
from django.contrib.auth.models import User
from faturas.service.compras_service import parcelar_compra, atualiza_fatura
from dateutil.relativedelta import relativedelta
from faturas.utils import mes_atua_dia11



def tratar_import_fatura(request, data):
    if data:
        itens_tratados = []
        usuario = User.objects.get(id=request.POST.get('usuario'))
        for item in data:
            nome_da_compra = item.get('nome_da_compra', 'Compra')
            data_compra = item.get('data_compra')
            parcela = item.get('parcela')
            valor_da_compra = str(item.get('valor_da_compra')).replace(' ', '').replace(',', '.')
            if valor_da_compra:
                compra_parcelada = False
                if parcela is not None:
                    parcela_atual, total_parcelas = parcela.split('|')
                    parcela_atual = int(parcela_atual)
                    total_parcelas = int(total_parcelas)
                    compra_parcelada = True
                    valor_da_compra = Decimal(valor_da_compra) * total_parcelas
                else:
                    parcela_atual = 'Única'
                    total_parcelas = 1
                if data_compra is None:
                    data_compra = mes_atua_dia11()
                if total_parcelas > 1 and parcela_atual > 1:
                    data_compra = data_compra - relativedelta(months=int(parcela_atual-1))
                    
                valor_da_compra = Decimal(valor_da_compra)
                
                compra_data = {
                    'usuario': usuario,
                    'nome_compra': nome_da_compra,
                    'n_parcelas': total_parcelas,
                    'valor_compra': valor_da_compra,
                    'data_compra': data_compra,
                    'cartao': '',
                    'compra_recorrente': False,
                    'compra_parcelada': compra_parcelada
                }

                form = CompraForm(compra_data)
                if form.is_valid():
                    compra = Compra.objects.create(**compra_data)
                    if total_parcelas > 1:
                        parcelar_compra(compra)
                    else:
                        compra.parcela_atual = 'Única'
                        compra.valor_parcela = compra.valor_compra
                        compra.data_parcela = compra.data_compra
                        atualiza_fatura(compra)
                    itens_tratados.append(compra_data)
                else:
                    raise ValueError(f"Erro ao criar compra: {compra_data}")
        return compra_data
    else:
        raise ValueError("Erro: Upload de dados não foi bem-sucedido.")


def gera_fatura(request, mes, ano):
    usuario = request.user
    faturas = Fatura.objects.filter(usuario=usuario, mes=mes, ano=ano)
    recorrente = Fatura.objects.filter(usuario=usuario, compra__compra_recorrente=True)
    if recorrente:
        faturas = faturas | recorrente
    compras = faturas.count()
    total = 0
    total = sum(fatura.valor_parcela for fatura in faturas)
    
    return faturas, total, compras
        