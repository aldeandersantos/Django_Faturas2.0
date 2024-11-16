from django import forms
from .models import Compra
from .models import ComprasParceladas

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['nome_compra', 'valor_compra', 'data_compra', 'n_parcelas', 'compra_recorrente', 'compra_parcelada']


class ComprasParceladasForm(forms.ModelForm):
    class Meta:
        model = ComprasParceladas
        fields = ['id_compra', 'nome_compra', 'usuario', 'data_compra', 'valor_parcela', 'parcela', 'total_parcelas']