from dateutil.relativedelta import relativedelta
from faturas.models import Compra, ComprasParceladas




def validar_compra(compra):
    if not compra.compra_parcelada and compra.n_parcelas != 1:
        return ('parcelas', 'Uma compra não parcelada deve ter apenas uma parcela.')

    if compra.compra_parcelada and compra.n_parcelas <= 1:
        return ('parcelas', 'Uma compra parcelada deve ter mais de uma parcela.')

    return None

def parcelar_compra(compra):
    usuario = compra.usuario
    n_parcelas = compra.n_parcelas
    valor_parcela = compra.valor_compra / n_parcelas
    data_parcela = compra.data_compra
    nome_compra = compra.nome_compra

    for i in range(n_parcelas):
        ComprasParceladas.objects.create(
            nome_compra=nome_compra,
            usuario=usuario,
            data_compra=data_parcela,
            valor_parcela=valor_parcela,
            parcela=i + 1,
            total_parcelas=n_parcelas
        )
        data_parcela += relativedelta(months=1)
        

def gera_fatura(request, mes, ano):
    usuario = request.user
    compras = Compra.objects.filter(usuario=usuario, data_compra__month=mes, data_compra__year=ano).exclude(compra_parcelada=True)
    compras_parceladas = ComprasParceladas.objects.filter(usuario=usuario, data_compra__month=mes, data_compra__year=ano)
    fatura = []
    total = 0
    for compra in compras:
        nome = compra.nome_compra
        valor = compra.valor_compra
        parcela = ''
        fatura.append((nome, valor, parcela))
        total += compra.valor_compra
        
    for compra in compras_parceladas:
        nome = compra.nome_compra
        valor = compra.valor_parcela
        parcela = f'{compra.parcela}/{compra.total_parcelas}'
        fatura.append((nome, valor, parcela))
        total += compra.valor_parcela
    return fatura, total
