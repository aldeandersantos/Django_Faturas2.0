import pytest
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from faturas.service.compras_service import salvar_compra
from faturas.models import Compra, Fatura
from django.test import RequestFactory
from faturas.views.compras_views import cadastrar_compra, cadastrar_compra_admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

pytestmark = pytest.mark.django_db

class TestCompras:
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

    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def get_request(self, request_factory, usuario):
        request = request_factory.get('/')
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.fixture
    def get_admin_request(self, request_factory, usuario_admin):
        request = request_factory.get('/')
        request.user = usuario_admin
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.fixture
    def post_request_compra(self, request_factory, usuario):
        data = {
            'nome_compra': 'Nova Compra Teste',
            'valor_compra': '200.00',
            'data_compra': '2024-04-15',
            'n_parcelas': '1',
            'cartao': 'Visa',
            'compra_recorrente': False,
            'compra_parcelada': False,
        }
        request = request_factory.post('/', data=data)
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.fixture
    def post_admin_request_compra(self, request_factory, usuario_admin, usuario):
        data = {
            'nome_compra': 'Compra Admin Teste',
            'valor_compra': '350.00',
            'data_compra': '2024-04-20',
            'n_parcelas': '1',
            'cartao': 'Master',
            'compra_recorrente': False,
            'compra_parcelada': False,
            'usuario': usuario.id
        }
        request = request_factory.post('/', data=data)
        request.user = usuario_admin
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        return request

    @pytest.mark.django_db
    def test_cadastrar_compra_view_get(self, get_request):
        # Act
        response = cadastrar_compra(get_request)
        
        # Assert
        assert response.status_code == 200
        # Verificando se há um formulário no conteúdo HTML
        assert b'<form' in response.content
        # Verificando se o HTML contém elementos típicos de uma página de cadastro
        assert b'name=' in response.content.lower()

    @pytest.mark.django_db
    def test_cadastrar_compra_view_post(self, post_request_compra):
        # Contagem de compras antes da execução
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra(post_request_compra)
        
        # Assert
        assert response.status_code == 200
        assert Compra.objects.count() == compras_antes + 1
        
        # Verifica se a compra foi salva corretamente
        nova_compra = Compra.objects.filter(nome_compra='Nova Compra Teste').first()
        assert nova_compra is not None
        assert nova_compra.valor_compra == Decimal('200.00')
        assert nova_compra.usuario == post_request_compra.user
        
        # Verifica se a fatura foi criada
        fatura = Fatura.objects.filter(compra=nova_compra).first()
        assert fatura is not None
        assert fatura.parcela_atual == 'Única'
        assert fatura.valor_parcela == nova_compra.valor_compra

    @pytest.mark.django_db
    def test_cadastrar_compra_view_post_invalido(self, request_factory, usuario):
        # Dados inválidos (nenhum dado fornecido - todos campos são obrigatórios)
        data = {
            # Propositalmente vazio para forçar erros de validação
        }
        request = request_factory.post('/', data=data)
        request.user = usuario
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        
        # Contagem de compras antes da execução
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra(request)
        
        # Assert
        assert response.status_code == 200
        # Nenhuma compra deve ser criada com dados inválidos
        assert Compra.objects.count() == compras_antes
        # Verificamos se há mensagens de erro no HTML
        assert b'form' in response.content
        assert b'error' in response.content.lower() or b'invalid' in response.content.lower()

    @pytest.mark.django_db
    def test_cadastrar_compra_admin_view_get(self, get_admin_request):
        # Act
        response = cadastrar_compra_admin(get_admin_request)
        
        # Assert
        assert response.status_code == 200
        # Verifica se há um formulário no conteúdo HTML
        assert b'<form' in response.content
        # Verifica se há opções de seleção de usuário
        assert b'usuario' in response.content.lower()

    @pytest.mark.django_db
    def test_cadastrar_compra_admin_view_post(self, post_admin_request_compra, usuario):
        # Contagem de compras antes da execução
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra_admin(post_admin_request_compra)
        
        # Assert
        assert response.status_code == 200
        assert Compra.objects.count() == compras_antes + 1
        
        # Verifica se a compra foi salva corretamente
        nova_compra = Compra.objects.filter(nome_compra='Compra Admin Teste').first()
        assert nova_compra is not None
        assert nova_compra.valor_compra == Decimal('350.00')
        assert nova_compra.usuario == usuario
        
        # Verifica se a fatura foi criada
        fatura = Fatura.objects.filter(compra=nova_compra).first()
        assert fatura is not None
        assert fatura.parcela_atual == 'Única'
        assert fatura.valor_parcela == nova_compra.valor_compra

    @pytest.mark.django_db
    def test_cadastrar_compra_admin_view_post_invalido(self, request_factory, usuario_admin, usuario):
        # Dados inválidos (apenas o ID do usuário é fornecido)
        data = {
            'usuario': usuario.id
            # Propositalmente vazio para forçar erros de validação
        }
        request = request_factory.post('/', data=data)
        request.user = usuario_admin
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        request._messages = FallbackStorage(request)
        
        # Contagem de compras antes da execução
        compras_antes = Compra.objects.count()
        
        # Act
        response = cadastrar_compra_admin(request)
        
        # Assert
        assert response.status_code == 200
        # Nenhuma compra deve ser criada com dados inválidos
        assert Compra.objects.count() == compras_antes
        # Verificamos se há mensagens de erro no HTML
        assert b'form' in response.content
        assert b'error' in response.content.lower() or b'invalid' in response.content.lower()

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
        assert fatura.mes == 4
        assert fatura.ano == 2024

    @pytest.mark.django_db
    def test_salvar_compra_parcelada(self, compra_base):
        # Arrange
        compra_base.n_parcelas = 3
        compra_base.data_compra = datetime.strptime("15/03/2024", "%d/%m/%Y").date()
        valor_esperado_parcela = Decimal('50.17')

        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        faturas = list(Fatura.objects.filter(compra=compra_atualizada).order_by('ano', 'mes'))
        
        assert compra_atualizada.compra_parcelada
        assert len(faturas) == 3
        
        assert faturas[0].valor_parcela == valor_esperado_parcela
        assert faturas[0].parcela_atual == "1/3"
        assert faturas[0].mes == 4 
        assert faturas[0].ano == 2024
        assert faturas[0].data_compra == datetime.strptime("15/04/2024", "%d/%m/%Y").date()

        assert faturas[1].valor_parcela == valor_esperado_parcela
        assert faturas[1].parcela_atual == "2/3"
        assert faturas[1].mes == 5
        assert faturas[1].ano == 2024
        assert faturas[1].data_compra == datetime.strptime("15/04/2024", "%d/%m/%Y").date()

        assert faturas[2].valor_parcela == valor_esperado_parcela
        assert faturas[2].parcela_atual == "3/3"
        assert faturas[2].mes == 6
        assert faturas[2].ano == 2024
        assert faturas[2].data_compra == datetime.strptime("15/04/2024", "%d/%m/%Y").date()

        assert all(f.valor_parcela == valor_esperado_parcela for f in faturas)

    @pytest.mark.django_db
    def test_salvar_compra_recorrente(self, compra_base):
        # Arrange
        compra_base.compra_recorrente = True
        data_esperada_compra = datetime(2000, 1, 1).date()

        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        fatura = Fatura.objects.get(compra=compra_atualizada)
        
        assert compra_atualizada.data_compra == data_esperada_compra
        assert fatura.parcela_atual == "Única"
        assert fatura.data_compra == data_esperada_compra
        assert fatura.valor_parcela == compra_base.valor_compra
        assert fatura.mes == 1
        assert fatura.ano == 2000

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
        data_compra_original = datetime.strptime("15/03/2024", "%d/%m/%Y").date()
        compra_base.data_compra = data_compra_original
        data_compra_esperada_na_compra = datetime.strptime("15/04/2024", "%d/%m/%Y").date()

        # Act
        salvar_compra(compra_base)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra_base.id)
        fatura = Fatura.objects.get(compra=compra_atualizada)

        assert compra_atualizada.data_compra == data_compra_esperada_na_compra
        
        assert fatura.parcela_atual == "Única"
        assert fatura.valor_parcela == compra_base.valor_compra
        assert fatura.data_compra == data_compra_esperada_na_compra
        assert fatura.mes == 4
        assert fatura.ano == 2024

    @pytest.mark.django_db
    def test_salvar_compra_parcelada_antes_dia_12(self, usuario):
        # Arrange
        compra = Compra(
            usuario=usuario,
            nome_compra="Compra Parcelada Antes Dia 12",
            valor_compra=Decimal('300.00'),
            data_compra=datetime.strptime("05/03/2024", "%d/%m/%Y").date(),
            n_parcelas=3,
            compra_recorrente=False,
            compra_parcelada=False,
            cartao="Visa"
        )
        compra.save()
        valor_esperado_parcela = Decimal('100.00')

        # Act
        salvar_compra(compra)

        # Assert
        compra_atualizada = Compra.objects.get(id=compra.id)
        faturas = list(Fatura.objects.filter(compra=compra_atualizada).order_by('ano', 'mes'))

        assert compra_atualizada.compra_parcelada
        assert len(faturas) == 3
        assert compra_atualizada.data_compra == datetime.strptime("05/03/2024", "%d/%m/%Y").date()

        assert faturas[0].parcela_atual == "1/3"
        assert faturas[0].valor_parcela == valor_esperado_parcela
        assert faturas[0].mes == 3
        assert faturas[0].ano == 2024
        assert faturas[0].data_compra == datetime.strptime("05/03/2024", "%d/%m/%Y").date()

        assert faturas[1].parcela_atual == "2/3"
        assert faturas[1].valor_parcela == valor_esperado_parcela
        assert faturas[1].mes == 4
        assert faturas[1].ano == 2024
        assert faturas[1].data_compra == datetime.strptime("05/03/2024", "%d/%m/%Y").date()

        assert faturas[2].parcela_atual == "3/3"
        assert faturas[2].valor_parcela == valor_esperado_parcela
        assert faturas[2].mes == 5
        assert faturas[2].ano == 2024
        assert faturas[2].data_compra == datetime.strptime("05/03/2024", "%d/%m/%Y").date()
