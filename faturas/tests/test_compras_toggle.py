import pytest
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from faturas.models import Compra, Fatura
from django.test import RequestFactory
from faturas.views.compras_views import cadastrar_compra, cadastrar_compra_admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

pytestmark = pytest.mark.django_db

class TestComprasToggleFeature:
    @pytest.fixture
    def usuario(self):
        return User.objects.create_user(
            username='testuser',
            password='12345'
        )

    @pytest.fixture
    def usuario_admin(self):
        admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        return admin

    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def post_request_valor_total(self, request_factory, usuario):
        # Test using total value mode (existing behavior)
        data = {
            'nome_compra': 'Compra Valor Total',
            'valor_compra': '300.00',
            'data_compra': '2024-04-15',
            'n_parcelas': '3',
            'cartao': 'Visa',
            'compra_recorrente': False,
            'compra_parcelada': False,
            'valor_type': 'total'  # Using total value mode
        }
        request = request_factory.post('/', data=data)
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.fixture  
    def post_request_valor_parcela(self, request_factory, usuario):
        # Test using installment value mode (new feature)
        data = {
            'nome_compra': 'Compra Valor Parcela',
            'valor_compra': '100.00',  # This is installment value
            'data_compra': '2024-04-15',
            'n_parcelas': '3',
            'cartao': 'Visa',
            'compra_recorrente': False,
            'compra_parcelada': False,
            'valor_type': 'parcela'  # Using installment value mode
        }
        request = request_factory.post('/', data=data)
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.fixture
    def post_admin_request_valor_parcela(self, request_factory, usuario_admin, usuario):
        # Test admin form with installment value mode
        data = {
            'nome_compra': 'Admin Compra Valor Parcela',
            'valor_compra': '150.00',  # This is installment value
            'data_compra': '2024-04-20',
            'n_parcelas': '2',
            'cartao': 'Master',
            'compra_recorrente': False,
            'compra_parcelada': False,
            'usuario': usuario.id,
            'valor_type': 'parcela'  # Using installment value mode
        }
        request = request_factory.post('/', data=data)
        request.user = usuario_admin
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.mark.django_db
    def test_compra_valor_total_mode(self, post_request_valor_total):
        """Test purchase with total value mode (R$ 300 total, 3 installments = R$ 100 each)"""
        # Arrange
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra(post_request_valor_total)
        
        # Assert - Should redirect after successful creation
        assert response.status_code == 302
        assert Compra.objects.count() == compras_antes + 1
        
        # Verify the purchase was saved correctly
        nova_compra = Compra.objects.filter(nome_compra='Compra Valor Total').first()
        assert nova_compra is not None
        assert nova_compra.valor_compra == Decimal('300.00')  # Total value
        assert nova_compra.n_parcelas == 3
        assert nova_compra.compra_parcelada == True  # Should be marked as installment purchase
        
        # Verify installments were created correctly
        faturas = Fatura.objects.filter(compra=nova_compra).order_by('mes')
        assert len(faturas) == 3
        
        # Each installment should be R$ 100 (300/3)
        expected_installment = Decimal('100.00')
        for fatura in faturas:
            assert fatura.valor_parcela == expected_installment

    @pytest.mark.django_db
    def test_compra_valor_parcela_mode(self, post_request_valor_parcela):
        """Test purchase with installment value mode (R$ 100 per installment, 3 installments = R$ 300 total)"""
        # Arrange
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra(post_request_valor_parcela)
        
        # Assert - Should redirect after successful creation
        assert response.status_code == 302
        assert Compra.objects.count() == compras_antes + 1
        
        # Verify the purchase was saved correctly
        nova_compra = Compra.objects.filter(nome_compra='Compra Valor Parcela').first()
        assert nova_compra is not None
        # The total value should be calculated as installment_value * n_installments
        assert nova_compra.valor_compra == Decimal('300.00')  # 100 * 3 = 300
        assert nova_compra.n_parcelas == 3
        assert nova_compra.compra_parcelada == True
        
        # Verify installments were created correctly
        faturas = Fatura.objects.filter(compra=nova_compra).order_by('mes')
        assert len(faturas) == 3
        
        # Each installment should be R$ 100 (the original input value)
        expected_installment = Decimal('100.00')
        for fatura in faturas:
            assert fatura.valor_parcela == expected_installment

    @pytest.mark.django_db
    def test_admin_compra_valor_parcela_mode(self, post_admin_request_valor_parcela, usuario):
        """Test admin purchase with installment value mode"""
        # Arrange
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra_admin(post_admin_request_valor_parcela)
        
        # Assert - Should redirect after successful creation
        assert response.status_code == 302
        assert Compra.objects.count() == compras_antes + 1
        
        # Verify the purchase was saved correctly
        nova_compra = Compra.objects.filter(nome_compra='Admin Compra Valor Parcela').first()
        assert nova_compra is not None
        # Total should be 150 * 2 = 300
        assert nova_compra.valor_compra == Decimal('300.00')
        assert nova_compra.n_parcelas == 2
        assert nova_compra.usuario == usuario
        
        # Verify installments
        faturas = Fatura.objects.filter(compra=nova_compra).order_by('mes')
        assert len(faturas) == 2
        
        # Each installment should be R$ 150
        expected_installment = Decimal('150.00')
        for fatura in faturas:
            assert fatura.valor_parcela == expected_installment

    @pytest.mark.django_db
    def test_compra_valor_parcela_single_installment(self, request_factory, usuario):
        """Test installment value mode with single installment (should work like total value)"""
        # Arrange
        data = {
            'nome_compra': 'Compra Única Parcela',
            'valor_compra': '250.00',
            'data_compra': '2024-04-15',
            'n_parcelas': '1',
            'cartao': 'Visa',
            'compra_recorrente': False,
            'compra_parcelada': False,
            'valor_type': 'parcela'
        }
        request = request_factory.post('/', data=data)
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        
        # Act
        response = cadastrar_compra(request)
        
        # Assert
        assert response.status_code == 302
        
        nova_compra = Compra.objects.filter(nome_compra='Compra Única Parcela').first()
        assert nova_compra is not None
        # For single installment, input value should equal total value
        assert nova_compra.valor_compra == Decimal('250.00')
        assert nova_compra.n_parcelas == 1
        assert nova_compra.compra_parcelada == False  # Single purchase, not installment
        
        # Should have only one invoice
        fatura = Fatura.objects.filter(compra=nova_compra).first()
        assert fatura is not None
        assert fatura.valor_parcela == Decimal('250.00')
        assert fatura.parcela_atual == 'Única'

    @pytest.mark.django_db
    def test_backwards_compatibility_no_valor_type(self, request_factory, usuario):
        """Test that requests without valor_type parameter work as before (total value mode)"""
        # Arrange - Don't include valor_type parameter (backwards compatibility)
        data = {
            'nome_compra': 'Compra Compatibilidade',
            'valor_compra': '400.00',
            'data_compra': '2024-04-15',
            'n_parcelas': '4',
            'cartao': 'Visa',
            'compra_recorrente': False,
            'compra_parcelada': False,
            # Notably missing: 'valor_type' parameter
        }
        request = request_factory.post('/', data=data)
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        
        # Act
        response = cadastrar_compra(request)
        
        # Assert - Should work as total value mode (existing behavior)
        assert response.status_code == 302
        
        nova_compra = Compra.objects.filter(nome_compra='Compra Compatibilidade').first()
        assert nova_compra is not None
        assert nova_compra.valor_compra == Decimal('400.00')  # Total value preserved
        assert nova_compra.n_parcelas == 4
        
        # Verify installments were calculated correctly (400/4 = 100 each)
        faturas = Fatura.objects.filter(compra=nova_compra).order_by('mes')
        assert len(faturas) == 4
        
        expected_installment = Decimal('100.00')
        for fatura in faturas:
            assert fatura.valor_parcela == expected_installment