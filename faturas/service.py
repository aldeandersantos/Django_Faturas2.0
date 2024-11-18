
from dateutil.relativedelta import relativedelta
from faturas.models import Compra, Fatura
from faturas.forms import FaturaForm


def salvar_compra(compra):
    if compra.data_compra.day >= 12:
        compra.data_compra += relativedelta(months=1)
    if compra.compra_recorrente:
        compra.data_compra = compra.data_compra.replace(year=2000, month=1, day=1)
        
    if compra.n_parcelas > 1:
        compra.compra_parcelada = True
        compra.save()
        parcelar_compra(compra)
    else:
        compra.save()
        compra.parcela_atual = 'Única'
        compra.valor_parcela = compra.valor_compra
        atualiza_fatura(compra)
    
def validar_compra(compra):
    if compra.compra_recorrente and compra.n_parcelas != 1:
        return ('n_parcelas', 'Uma compra recorrente não pode ser parcelada.')
    return None

def parcelar_compra(compra):
    n_parcelas = int(compra.n_parcelas)
    compra.valor_parcela = int(compra.valor_compra / n_parcelas)
    compra.parcela = 0

    for i in range(n_parcelas):
        compra.parcela = i + 1
        compra.parcela_atual = f'{compra.parcela}/{n_parcelas}'
        atualiza_fatura(compra)
        compra.data_compra += relativedelta(months=1)
        

def atualiza_fatura(compra):
    fatura_data = {
        'usuario': compra.usuario,
        'compra': compra,
        'nome_compra': compra.nome_compra,
        'parcela_atual': compra.parcela_atual,
        'valor_parcela': compra.valor_parcela,
        'valor_compra': compra.valor_compra,
        'data_compra': compra.data_compra,
        'mes': compra.data_compra.month,
        'ano': compra.data_compra.year
    }
    fatura_form = FaturaForm(fatura_data)
    if fatura_form.is_valid():
        fatura_form.save()
    else:
        raise ValueError(f"Erro ao criar fatura: {fatura_form.errors}")


def gera_fatura(request, mes, ano):
    usuario = request.user
    faturas = Fatura.objects.filter(usuario=usuario, mes=mes, ano=ano)
    recorrente = Fatura.objects.filter(usuario=usuario, compra__compra_recorrente=True)
    if recorrente:
        
        faturas = faturas | recorrente
    total = sum(fatura.valor_parcela for fatura in faturas)
    return faturas, total