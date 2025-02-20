import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from documentos.models import UserFile
from documentos.tests.utils import carregar_dados_teste

pytestmark = pytest.mark.django_db

class TestUserFileModel:
    @pytest.fixture
    def dados_usuarios(self):
        return carregar_dados_teste('usuarios.json')

    @pytest.fixture
    def usuario(self, dados_usuarios):
        dados = dados_usuarios['usuario_padrao']
        return User.objects.create_user(**dados)

    @pytest.fixture
    def arquivo_teste(self):
        return SimpleUploadedFile(
            "arquivo_teste.txt",
            b"Conteudo do arquivo de teste",
            content_type="text/plain"
        )

    @pytest.fixture
    def arquivo_base(self, usuario, arquivo_teste):
        user_file = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_teste,
            texto="Descrição do arquivo",
            tipo="arquivo"
        )
        return user_file

    def test_criar_arquivo(self, usuario, arquivo_teste):
        arquivo = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_teste,
            texto="Teste de upload",
            tipo="arquivo"
        )
        assert arquivo.texto == "Teste de upload"
        assert arquivo.tipo == "arquivo"

    def test_deletar_arquivo(self, arquivo_base):
        arquivo_id = arquivo_base.id
        arquivo_base.delete()
        assert not UserFile.objects.filter(id=arquivo_id).exists()

    def test_criar_arquivo_com_mesmo_nome(self, usuario, arquivo_teste):
        UserFile.objects.create(
            usuario=usuario,
            file=arquivo_teste,
            tipo="arquivo"
        )
        
        arquivo_duplicado = SimpleUploadedFile(
            "arquivo_teste.txt",
            b"Outro conteudo",
            content_type="text/plain"
        )
        
        arquivo2 = UserFile.objects.create(
            usuario=usuario,
            file=arquivo_duplicado,
            tipo="arquivo"
        )
        
        assert "arquivo_teste_" in arquivo2.file.name
        assert arquivo2.file.name != arquivo_teste.name

    def test_validacao_tipo_arquivo(self, usuario, arquivo_teste):
        arquivo = UserFile(
            usuario=usuario,
            file=arquivo_teste,
            tipo="tipo_invalido"
        )
        with pytest.raises(ValidationError):
            arquivo.full_clean()

    def test_str_representation(self, arquivo_base):
        assert str(arquivo_base) == f"{arquivo_base.usuario.username} - {arquivo_base.file.name}"

    def test_arquivo_sem_usuario(self, arquivo_teste):
        arquivo = UserFile(
            file=arquivo_teste,
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