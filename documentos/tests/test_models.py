import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from documentos.models import UserFile
from documentos.tests.utils import carregar_dados_teste
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestUserFileModel:
    @pytest.fixture
    def dados_usuarios(self):
        return carregar_dados_teste('usuarios.json')

    @pytest.fixture
    def usuario(self, dados_usuarios):
        dados = dados_usuarios['usuario_padrao']
        return User.objects.create_user(**dados)

    @pytest.fixture
    def arquivo_mock(self):
        return SimpleUploadedFile(
            "arquivo_teste.txt",
            b"Conteudo do arquivo de teste",
            content_type="text/plain"
        )

    @pytest.fixture
    def arquivo_base(self, usuario, arquivo_mock):
        user_file = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_mock,
            texto="Descrição do arquivo",
            tipo="arquivo"
        )
        return user_file

    def test_criar_arquivo(self, usuario, arquivo_mock):
        arquivo = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_mock,
            texto="Teste de upload",
            tipo="arquivo"
        )
        assert arquivo.texto == "Teste de upload"
        assert arquivo.tipo == "arquivo"

    def test_deletar_arquivo(self, arquivo_base):
        arquivo_id = arquivo_base.id
        arquivo_base.delete()
        assert not UserFile.objects.filter(id=arquivo_id).exists()

    def test_criar_arquivo_com_mesmo_nome(self, usuario, arquivo_mock):
        primeiro_arquivo = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_mock,
            tipo="arquivo"
        )
        
        arquivo_duplicado = SimpleUploadedFile(
            "arquivo_teste.txt",
            b"Outro conteudo",
            content_type="text/plain"
        )
        
        segundo_arquivo = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_duplicado,
            tipo="arquivo"
        )
        
        assert primeiro_arquivo.file.name != segundo_arquivo.file.name

    def test_validacao_tipo_arquivo(self, usuario, arquivo_mock):
        arquivo = UserFile(
            usuario=usuario,
            file=arquivo_mock,
            tipo="tipo_invalido"
        )
        with pytest.raises(ValidationError):
            arquivo.full_clean()

    def test_str_representation(self, arquivo_base):
        assert str(arquivo_base).startswith(f"{arquivo_base.usuario.username} - ")
        assert "arquivo_teste.txt" in str(arquivo_base)

    def test_arquivo_sem_usuario(self, arquivo_mock):
        arquivo = UserFile(
            file=arquivo_mock,
            tipo="arquivo"
        )
        with pytest.raises(ValidationError):
            arquivo.full_clean()

    def test_upload_arquivo_invalido(self, usuario):
        arquivo = UserFile(
            usuario=usuario,
            file=None,
            tipo="arquivo"
        )
        with pytest.raises(ValidationError):
            arquivo.full_clean()