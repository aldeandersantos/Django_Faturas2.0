from django.urls import path
from documentos.views import *

app_name = 'documentos'

urlpatterns = [
    path('upload', upload_arquivo, name='upload_arquivo'),
    path('arquivos', listar_arquivos, name='arquivos'),
]