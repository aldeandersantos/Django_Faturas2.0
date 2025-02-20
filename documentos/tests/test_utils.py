import pytest
from documentos.utils import get_file_icon

class TestFileUtils:
    @pytest.mark.parametrize("nome_arquivo,icone_esperado", [
        ("documento.pdf", "fa-file-pdf"),
        ("planilha.xlsx", "fa-file-excel"),
        ("imagem.jpg", "fa-file-image"),
        ("codigo.py", "fa-file-code"),
        ("arquivo.txt", "fa-file-alt"),
        ("video.mp4", "fa-file-video"),
        ("musica.mp3", "fa-file-audio"),
        ("compactado.zip", "fa-file-archive"),
        ("arquivo_sem_extensao", "fa-file"),
    ])
    def test_icones_arquivo(self, nome_arquivo, icone_esperado):
        assert get_file_icon(nome_arquivo) == icone_esperado 