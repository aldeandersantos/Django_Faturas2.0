import pytest
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from faturas.service.compras_service import salvar_compra
from faturas.models import Compra, Fatura

pytestmark = pytest.mark.django_db  # Marca todos os testes para usar o banco de dados

class TestCompras:
    @pytest.fixture
    def usuario(self):
        return User.objects.create_user(
            username='testuser',
            password='12345'
        )

    @pytest.fixture
    def compra_base(self, usuario):
        compra = Compra(
            usuario=usuario,
            nome_compra="Supermercado Exemplo",
            valor_compra=Decimal('150.50'),
            data_compra=datetime.strptime("15/03/2024", "%d/%m/%Y"),
            n_parcelas=1,
            compra_recorrente=False,
            compra_parcelada=False,
            cartao="Master"
        )
        compra.save()  # Salva a compra no banco
        return compra

    @pytest.mark.django_db
    def test_salvar_compra_unica(self, compra_base):
        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        fatura = Fatura.objects.get(compra=compra_atualizada)
        
        assert not compra_atualizada.compra_parcelada
        assert fatura.parcela_atual == "Única"
        assert fatura.valor_parcela == Decimal('150.50')
        assert fatura.data_compra == compra_atualizada.data_compra

    @pytest.mark.django_db
    def test_salvar_compra_parcelada(self, compra_base):
        # Arrange
        compra_base.n_parcelas = 3
        valor_esperado_parcela = Decimal('50.17')  # 150.50 / 3 arredondado

        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        faturas = Fatura.objects.filter(compra=compra_atualizada)
        
        assert compra_atualizada.compra_parcelada
        assert faturas.count() == 3  # Deve criar 3 faturas
        assert faturas.first().valor_parcela == valor_esperado_parcela
        assert all(f.valor_parcela == valor_esperado_parcela for f in faturas)

    @pytest.mark.django_db
    def test_salvar_compra_recorrente(self, compra_base):
        # Arrange
        compra_base.compra_recorrente = True
        data_esperada = datetime(2000, 1, 1).date()

        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        fatura = Fatura.objects.get(compra=compra_atualizada)
        
        assert compra_atualizada.data_compra == data_esperada
        assert fatura.parcela_atual == "Única"

    @pytest.mark.django_db
    def test_validar_compra_recorrente_parcelada(self, compra_base):
        # Arrange
        compra_base.compra_recorrente = True
        compra_base.n_parcelas = 3

        # Act
        from faturas.service.compras_service import validar_compra
        resultado = validar_compra(compra_base)

        # Assert
        assert resultado == ('n_parcelas', 'Uma compra recorrente não pode ser parcelada.')

    @pytest.mark.django_db
    def test_salvar_compra_apos_dia_12(self, compra_base):
        # Arrange
        data_compra = datetime.strptime("15/03/2024", "%d/%m/%Y").date()
        compra_base.data_compra = data_compra
        data_esperada = datetime.strptime("15/04/2024", "%d/%m/%Y").date()

        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        assert compra_atualizada.data_compra == data_esperada
