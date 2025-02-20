import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from documentos.models import UserFile
from documentos.tests.utils import carregar_dados_teste

@pytest.fixture
def dados_usuarios():
    return carregar_dados_teste('usuarios.json')

@pytest.fixture
def dados_arquivos():
    return carregar_dados_teste('arquivos.json')

@pytest.fixture
def usuario(dados_usuarios):
    dados = dados_usuarios['usuario_padrao']
    return User.objects.create_user(**dados)

@pytest.fixture
def arquivo_teste():
    return SimpleUploadedFile(
        "arquivo_teste.txt",
        b"Conteudo do arquivo de teste",
        content_type="text/plain"
    )

@pytest.fixture
def arquivo_base(usuario, arquivo_teste):
    user_file = UserFile.objects.create(
        usuario=usuario,
        file=arquivo_teste,
        texto="Descrição do arquivo",
        tipo="arquivo"
    )
    return user_file

@pytest.fixture
def client_autenticado(client, usuario):
    client.force_login(usuario)
    return client 