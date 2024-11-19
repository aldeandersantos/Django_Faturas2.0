from django import forms
from .models import Compra
from .models import Fatura

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['nome_compra', 'valor_compra', 'data_compra', 'n_parcelas', 'compra_recorrente', 'compra_parcelada', 'cartao']

class FaturaForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ['usuario', 'compra', 'nome_compra', 'parcela_atual', 'valor_parcela', 'valor_compra', 'data_compra', 'mes', 'ano']