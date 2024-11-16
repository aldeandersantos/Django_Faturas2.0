from django.db import models
from django.contrib.auth.models import User
from faturas.utils import hoje



class Compra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome_compra = models.CharField(max_length=100, blank=False, null=False, default='')
    valor_compra = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    data_compra = models.DateField(default=hoje, blank=False, null=False)
    n_parcelas = models.PositiveIntegerField(default=1, blank=False, null=False)
    compra_recorrente = models.BooleanField(default=False)
    compra_parcelada = models.BooleanField(default=False)

    @property
    def total(self):
        return self.nome_compra * self.valor_compra

    def __str__(self):
        return f"{self.nome_compra} - {self.usuario.username}"


class ComprasParceladas(models.Model):
    id_compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome_compra = models.CharField(max_length=100, blank=False, null=False, default='')
    data_compra = models.DateField()
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    parcela = models.PositiveIntegerField(default=None)
    total_parcelas = models.PositiveIntegerField(default=None)

    def __str__(self):
        return f"Parcela de {self.nome_compra} - {self.usuario.username} - {self.data_compra}"
