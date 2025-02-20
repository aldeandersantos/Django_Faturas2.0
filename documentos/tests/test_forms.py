import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from documentos.forms import FileUploadForm

pytestmark = pytest.mark.django_db

class TestFileUploadForm:
    @pytest.fixture
    def arquivo_teste(self):
        return SimpleUploadedFile(
            "arquivo_teste.txt",
            b"Conteudo do arquivo de teste",
            content_type="text/plain"
        )

    @pytest.fixture
    def dados_form_validos(self, arquivo_teste):
        return {
            'file': arquivo_teste,
            'tipo': 'arquivo',
            'texto': 'Descrição do arquivo'
        }

    def test_form_valido(self, dados_form_validos):
        form = FileUploadForm(
            files={'file': dados_form_validos['file']},
            data={
                'tipo': dados_form_validos['tipo'],
                'texto': dados_form_validos['texto']
            }
        )
        assert form.is_valid()

    def test_form_sem_arquivo(self):
        form = FileUploadForm(
            data={
                'tipo': 'arquivo',
                'texto': 'Descrição'
            }
        )
        assert not form.is_valid()
        assert 'file' in form.errors

    def test_form_tipo_invalido(self, arquivo_teste):
        form = FileUploadForm(
            files={'file': arquivo_teste},
            data={
                'tipo': 'tipo_invalido',
                'texto': 'Descrição'
            }
        )
        assert not form.is_valid()
        assert 'tipo' in form.errors 