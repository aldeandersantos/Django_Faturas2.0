import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from documentos.models import UserFile
from documentos.tests.utils import carregar_dados_teste
from time import sleep

pytestmark = pytest.mark.django_db

class TestViewsGet:
    @pytest.fixture
    def usuario(self, dados_usuarios):
        dados = dados_usuarios['usuario_padrao']
        return User.objects.create_user(**dados)

    @pytest.fixture
    def client_autenticado(self, client, usuario):
        client.force_login(usuario)
        return client

    def test_acesso_nao_autenticado(self, client):
        response = client.get(reverse('documentos:gerenciar_arquivos'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_listar_arquivos(self, client_autenticado, arquivo_base):
        response = client_autenticado.get(reverse('documentos:gerenciar_arquivos'))
        assert response.status_code == 200
        assert arquivo_base.file.name in str(response.content)

    def test_filtro_tipo_arquivo(self, client_autenticado, arquivo_base):
        arquivo_base.tipo = 'texto'
        arquivo_base.save()
        response = client_autenticado.get(reverse('documentos:gerenciar_arquivos'))
        assert response.status_code == 200
        assert arquivo_base.file.name not in str(response.content)

    def test_ordenacao_arquivos(self, client_autenticado, usuario, arquivo_teste):
        # Arrange
        arquivo1 = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_teste,
            tipo="arquivo",
            texto="Primeiro arquivo"
        )
        
        # Pequeno delay para garantir ordem
        sleep(1)
        
        arquivo2 = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_teste,
            tipo="arquivo",
            texto="Segundo arquivo"
        )

        # Act
        response = client_autenticado.get(reverse('documentos:gerenciar_arquivos'))
        
        # Assert
        # Verifica se ambos os arquivos estão presentes
        content = str(response.content)
        assert "Primeiro arquivo" in content
        assert "Segundo arquivo" in content
        # Verifica se o segundo arquivo aparece primeiro na lista
        assert content.index("Segundo arquivo") < content.index("Primeiro arquivo") 