import pytest
from django.urls import reverse
from documentos.models import UserFile

pytestmark = pytest.mark.django_db

class TestViewsPost:
    def test_upload_arquivo(self, client_autenticado, arquivo_teste):
        data = {
            'file': arquivo_teste,
            'tipo': 'arquivo',
            'texto': 'Teste de upload via view'
        }
        response = client_autenticado.post(
            reverse('documentos:gerenciar_arquivos'),
            data=data
        )
        assert response.status_code == 302
        assert UserFile.objects.filter(texto='Teste de upload via view').exists()

    def test_upload_arquivo_htmx(self, client_autenticado, arquivo_teste):
        data = {
            'file': arquivo_teste,
            'tipo': 'arquivo',
            'texto': 'Teste HTMX'
        }
        response = client_autenticado.post(
            reverse('documentos:gerenciar_arquivos'),
            data=data,
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200
        assert UserFile.objects.filter(texto='Teste HTMX').exists()

    def test_upload_arquivo_invalido(self, client_autenticado):
        data = {
            'tipo': 'arquivo',
            'texto': 'Teste sem arquivo'
        }

        response = client_autenticado.post(
            reverse('documentos:gerenciar_arquivos'),
            data=data,
            HTTP_HX_REQUEST='true'
        )

        assert response.status_code == 200
        assert 'form-group' in str(response.content)
        assert 'alert-danger' in str(response.content)

    def test_mensagens_feedback(self, client_autenticado, arquivo_teste):
        data = {
            'file': arquivo_teste,
            'tipo': 'arquivo',
            'texto': 'Teste mensagens'
        }

        response = client_autenticado.post(
            reverse('documentos:gerenciar_arquivos'),
            data=data
        )

        messages = list(response.wsgi_request._messages)
        assert len(messages) > 0
        assert "sucesso" in str(messages[0]).lower() 