from dateutil.relativedelta import relativedelta
from faturas.models import Compra, ComprasParceladas
from faturas.forms import ComprasParceladasForm



def validar_compra(compra):
    if compra.compra_recorrente and compra.n_parcelas != 1:
        return ('n_parcelas', 'Uma compra recorrente não pode ser parcelada.')
    return None

def parcelar_compra(compra):
    usuario = compra.usuario
    n_parcelas = int(compra.n_parcelas)
    valor_parcela = int(compra.valor_compra / n_parcelas)
    data_parcela = compra.data_compra
    nome_compra = compra.nome_compra
    id_compra = compra.id

    for i in range(n_parcelas):
        print(usuario)
        form_data = {
            'id_compra': id_compra,
            'nome_compra': nome_compra,
            'usuario': usuario,
            'data_compra': data_parcela,
            'valor_parcela': valor_parcela,
            'parcela': i + 1,
            'total_parcelas': n_parcelas
        }
        form = ComprasParceladasForm(form_data)
        if form.is_valid():
            form.save()
        else:
            raise ValueError(f"Erro ao salvar parcela: {form.errors}, {form_data}")
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
