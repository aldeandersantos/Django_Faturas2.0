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
        
        # Verifica detalhes da fatura recuperada
        fatura = faturas[0]
        assert fatura.nome_compra == "Supermercado Exemplo"
        assert fatura.valor_parcela == Decimal('150.50')
        assert fatura.parcela_atual == "Única"
        assert fatura.mes == 3
        assert fatura.ano == 2024
        assert fatura.data_compra == datetime.strptime("2024-03-15", "%Y-%m-%d").date()

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
        
        # Verifica se as faturas específicas esperadas estão incluídas
        faturas_nome = [f.nome_compra for f in faturas]
        assert "Supermercado Exemplo" in faturas_nome
        assert "Netflix" in faturas_nome
        
        # Verifica a fatura recorrente especificamente
        fatura_netflix = next(f for f in faturas if f.nome_compra == "Netflix")
        assert fatura_netflix.valor_parcela == Decimal('45.90')
        assert fatura_netflix.valor_compra == Decimal('45.90')
        assert fatura_netflix.parcela_atual == "Única"
        assert fatura_netflix.data_compra == datetime(2000, 1, 1).date()
        assert fatura_netflix.mes == 3  # Aparece na fatura de março mesmo com data de 01/01/2000
        assert fatura_netflix.ano == 2024  # Aparece na fatura do ano atual

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

        # Verifica o dicionário retornado
        assert resultado['nome_compra'] == dados['fatura_unica']['nome_da_compra']
        assert resultado['valor_compra'] == Decimal(dados['fatura_unica']['valor_da_compra'].replace(',', '.'))
        assert not resultado['compra_parcelada']
        
        # Verifica a compra real salva no banco
        compra = Compra.objects.filter(nome_compra=dados['fatura_unica']['nome_da_compra']).first()
        assert compra is not None
        assert compra.valor_compra == Decimal(dados['fatura_unica']['valor_da_compra'].replace(',', '.'))
        assert not compra.compra_parcelada
        assert compra.n_parcelas == 1
        
        # Verifica a fatura criada
        fatura = Fatura.objects.filter(compra=compra).first()
        assert fatura is not None
        assert fatura.parcela_atual == "Única"
        assert fatura.valor_parcela == compra.valor_compra
        # A data na fatura depende da implementação de mes_atua_dia11() 
        # se não tiver data_compra na importação

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

        # Verifica o dicionário retornado
        assert resultado['nome_compra'] == dados['fatura_parcelada']['nome_da_compra']
        assert resultado['valor_compra'] == Decimal('150.51')  # 50.17 * 3 parcelas
        assert resultado['compra_parcelada']
        assert resultado['n_parcelas'] == 3
        
        # Verifica a compra real salva no banco
        compra = Compra.objects.filter(nome_compra=dados['fatura_parcelada']['nome_da_compra']).first()
        assert compra is not None
        assert compra.valor_compra == Decimal('150.51')
        assert compra.compra_parcelada
        assert compra.n_parcelas == 3
        
        # Verifica as faturas criadas
        faturas = list(Fatura.objects.filter(compra=compra).order_by('ano', 'mes'))
        assert len(faturas) == 3
        
        # Verifica o valor da parcela
        valor_esperado_parcela = Decimal('50.17')
        assert all(f.valor_parcela == valor_esperado_parcela for f in faturas)
        
        # Verifica as numerações das parcelas
        assert faturas[0].parcela_atual == "1/3"
        assert faturas[1].parcela_atual == "2/3"
        assert faturas[2].parcela_atual == "3/3"
        
        # Verifica os meses de cada parcela
        # Importante! O comportamento atual de data_compra define como a fatura é distribuída
        data_compra_atual = datetime.strptime(dados['fatura_parcelada']['data_compra'], "%Y-%m-%d").date()
        mes_parcela1 = data_compra_atual.month
        
        assert faturas[0].mes == mes_parcela1
        # Verificando também se a sequência de meses está correta
        assert (faturas[1].mes == mes_parcela1 + 1) or (faturas[1].mes == 1 and faturas[1].ano > faturas[0].ano)
        # Se o mês da parcela 2 for janeiro, o ano deve ter avançado
        if faturas[1].mes == 1:
            assert faturas[1].ano > faturas[0].ano
        
        # A terceira parcela segue o mesmo raciocínio
        assert (faturas[2].mes == faturas[1].mes + 1) or (faturas[2].mes == 1 and faturas[2].ano > faturas[1].ano)