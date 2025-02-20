import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from documentos.models import UserFile

pytestmark = pytest.mark.django_db

class TestViewsDelete:
    def test_deletar_arquivo(self, client_autenticado, arquivo_base):
        response = client_autenticado.delete(
            reverse('documentos:deletar_arquivo', args=[arquivo_base.id]),
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200
        assert not UserFile.objects.filter(id=arquivo_base.id).exists()

    def test_deletar_arquivo_outro_usuario(self, client_autenticado, arquivo_base):
        outro_usuario = User.objects.create_user('outro', 'senha123')
        arquivo_base.usuario = outro_usuario
        arquivo_base.save()

        response = client_autenticado.delete(
            reverse('documentos:deletar_arquivo', args=[arquivo_base.id])
        )

        assert response.status_code == 404
        assert UserFile.objects.filter(id=arquivo_base.id).exists() 