from django.urls import path
from documentos.views import *

app_name = 'documentos'

urlpatterns = [
    path('arquivos', gerenciar_arquivos, name='gerenciar_arquivos'),
    path('arquivos/<int:arquivo_id>', deletar_arquivo, name='deletar_arquivo'),
]