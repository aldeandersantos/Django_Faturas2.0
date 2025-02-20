import pytest
from django.contrib.auth.models import User
from faturas.service.usuario_service import registra_usuario
from django.contrib.messages.storage.fallback import FallbackStorage

pytestmark = pytest.mark.django_db

class TestUsuario:
    @pytest.fixture
    def mock_request(self):
        class MockRequest:
            def __init__(self):
                self.POST = {}
                self.session = {}
                self._messages = FallbackStorage(self)
                self.method = 'POST'
        return MockRequest()

    def test_registrar_usuario_com_sucesso(self, mock_request, load_fixture):
        dados = load_fixture('usuarios')
        mock_request.POST = dados['usuario_novo']
        resultado = registra_usuario(mock_request)

        assert resultado is None
        usuario = User.objects.get(email=dados['usuario_novo']['email'])
        assert usuario.first_name == dados['usuario_novo']['first_name']
        assert usuario.last_name == dados['usuario_novo']['last_name']
        assert usuario.username == 'joao.silva'

    def test_registrar_usuario_senhas_diferentes(self, mock_request, load_fixture):
        dados = load_fixture('usuarios')
        mock_request.POST = dados['usuario_senhas_diferentes']
        resultado = registra_usuario(mock_request)

        assert resultado == mock_request
        assert not User.objects.filter(email=dados['usuario_senhas_diferentes']['email']).exists()

    def test_registrar_usuario_email_existente(self, mock_request, load_fixture):
        dados = load_fixture('usuarios')
        User.objects.create_user(
            username='joao.silva',
            email=dados['usuario_novo']['email'],
            password='senha123'
        )
        
        mock_request.POST = dados['usuario_novo']
        resultado = registra_usuario(mock_request)

        assert resultado == mock_request
        assert User.objects.filter(email=dados['usuario_novo']['email']).count() == 1 