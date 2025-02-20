import pytest
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from faturas.models import Compra, Fatura
from faturas.service.fatura_service import gera_fatura, tratar_import_fatura

pytestmark = pytest.mark.django_db

class TestFaturas:
    @pytest.fixture
    def usuario(self):
        return User.objects.create_user(
            username='testuser',
            password='12345'
        )

    @pytest.fixture
    def compra_base(self, usuario):
        return Compra.objects.create(
            usuario=usuario,
            nome_compra="Supermercado Exemplo",
            valor_compra=Decimal('150.50'),
            data_compra=datetime.strptime("2024-03-15", "%Y-%m-%d"),
            n_parcelas=1,
            compra_recorrente=False,
            compra_parcelada=False,
            cartao="Master"
        )

    @pytest.fixture
    def fatura_base(self, usuario, compra_base):
        return Fatura.objects.create(
            usuario=usuario,
            compra=compra_base,
            nome_compra=compra_base.nome_compra,
            parcela_atual="Única",
            valor_parcela=compra_base.valor_compra,
            valor_compra=compra_base.valor_compra,
            data_compra=compra_base.data_compra,
            mes=3,
            ano=2024
        )

    def test_gera_fatura_mes_especifico(self, usuario, fatura_base):
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(usuario)
        faturas, total, compras = gera_fatura(request, mes=3, ano=2024)

        assert compras == 1
        assert total == Decimal('150.50')
        assert len(faturas) == 1
        assert faturas[0].valor_parcela == Decimal('150.50')

    def test_gera_fatura_com_compra_recorrente(self, usuario, compra_base, fatura_base):
        compra_recorrente = Compra.objects.create(
            usuario=usuario,
            nome_compra="Netflix",
            valor_compra=Decimal('45.90'),
            data_compra=datetime(2000, 1, 1),
            n_parcelas=1,
            compra_recorrente=True,
            compra_parcelada=False,
            cartao="Master"
        )
        
        Fatura.objects.create(
            usuario=usuario,
            compra=compra_recorrente,
            nome_compra=compra_recorrente.nome_compra,
            parcela_atual="Única",
            valor_parcela=compra_recorrente.valor_compra,
            valor_compra=compra_recorrente.valor_compra,
            data_compra=compra_recorrente.data_compra,
            mes=3,
            ano=2024
        )

        request = type('MockRequest', (), {'user': usuario})()
        faturas, total, compras = gera_fatura(request, mes=3, ano=2024)

        assert compras == 2
        assert total == Decimal('196.40')
        assert len(faturas) == 2

    def test_tratar_import_fatura_unica(self, usuario, load_fixture):
        dados = load_fixture('faturas')
        data = [{
            'nome_da_compra': dados['fatura_unica']['nome_da_compra'],
            'data_compra': datetime.strptime(dados['fatura_unica']['data_compra'], "%Y-%m-%d").date(),
            'parcela': dados['fatura_unica']['parcela'],
            'valor_da_compra': dados['fatura_unica']['valor_da_compra']
        }]
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.POST = {'usuario': user.id}
                self.method = 'POST'
        
        request = MockRequest(usuario)
        resultado = tratar_import_fatura(request, data)

        assert resultado['nome_compra'] == dados['fatura_unica']['nome_da_compra']
        assert resultado['valor_compra'] == Decimal(dados['fatura_unica']['valor_da_compra'].replace(',', '.'))
        assert not resultado['compra_parcelada']

    def test_tratar_import_fatura_parcelada(self, usuario, load_fixture):
        dados = load_fixture('faturas')
        data = [{
            'nome_da_compra': dados['fatura_parcelada']['nome_da_compra'],
            'data_compra': datetime.strptime(dados['fatura_parcelada']['data_compra'], "%Y-%m-%d").date(),
            'parcela': dados['fatura_parcelada']['parcela'],
            'valor_da_compra': dados['fatura_parcelada']['valor_da_compra']
        }]
        
        request = type('MockRequest', (), {
            'POST': {'usuario': usuario.id},
            'user': usuario,
            'method': 'POST'
        })()

        resultado = tratar_import_fatura(request, data)

        assert resultado['nome_compra'] == dados['fatura_parcelada']['nome_da_compra']
        assert resultado['valor_compra'] == Decimal('150.51')
        assert resultado['compra_parcelada']
        assert resultado['n_parcelas'] == 3 