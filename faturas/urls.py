from django.urls import path
from faturas.views import *

app_name = 'faturas'

urlpatterns = [
    path('', home, name='home'),
    path('cadastrar/', cadastrar_compra, name='cadastrar_compra'),
    path('lista/', ver_compras, name='lista_compras'),
    path('fatura/', ver_fatura, name='ver_fatura'),
    path('deletar/<int:id>/', deletar_compra, name='deletar_compra'),
    path('exportar_fatura/', exportar_fatura_excel, name='exportar_fatura'),
    path('cadastrar_admin/', cadastrar_compra_admin, name='cadastrar_compra_admin'),
    path('register', registrar_usuario, name='register'),
]
