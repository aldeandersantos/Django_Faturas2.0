from django.urls import path
from faturas.views import *

app_name = 'faturas'

urlpatterns = [
    path('', home, name='home'),
    path('cadastrar/', cadastrar_compra, name='cadastrar_compra'),
    path('lista/', lista_compras, name='lista_compras'),
    path('fatura/<int:mes>/<int:ano>/', ver_fatura, name='ver_fatura'),
    path('deletar/<int:id>/', deletar_compra, name='deletar_compra'),
]
