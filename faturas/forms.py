from django import forms
from .models import Compra

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['nome_compra', 'valor_compra', 'data_compra', 'parcelas', 'compra_recorrente', 'compra_parcelada']
