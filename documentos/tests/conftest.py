import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from documentos.models import UserFile
from documentos.tests.utils import carregar_dados_teste
from django.core.files.storage import Storage
from unittest.mock import patch

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

class MockStorage(Storage):
    def __init__(self):
        self.files = {}
        self.counter = 0

    def _save(self, name, content):
        while name in self.files:
            name_parts = name.rsplit('.', 1)
            if len(name_parts) > 1:
                name = f"{name_parts[0]}_{self.counter}.{name_parts[1]}"
            else:
                name = f"{name}_{self.counter}"
            self.counter += 1
        self.files[name] = content
        return name

    def delete(self, name):
        if name in self.files:
            del self.files[name]

    def exists(self, name):
        return name in self.files

    def url(self, name):
        return f"http://mocked-url/{name}"

@pytest.fixture(autouse=True)
def mock_storage():
    with patch('django.core.files.storage.default_storage._wrapped', MockStorage()):
        yield 