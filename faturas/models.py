from django.db import models
from django.contrib.auth.models import User
from faturas.utils import hoje



class Compra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome_compra = models.CharField(max_length=100, blank=False, null=False, default='')
    valor_compra = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    data_compra = models.DateField(default=hoje, blank=False, null=False)
    parcelas = models.PositiveIntegerField(default=1, blank=False, null=False)
    compra_recorrente = models.BooleanField(default=False)
    compra_parcelada = models.BooleanField(default=False)

    @property
    def total(self):
        return self.nome_compra * self.valor_compra

    def __str__(self):
        return f"{self.nome_compra} - {self.usuario.username}"


class Fatura(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    mes = models.IntegerField()
    ano = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calcular_total(self):
        compras = Compra.objects.filter(usuario=self.usuario, data_compra__month=self.mes, data_compra__year=self.ano)
        self.total = sum(compra.total for compra in compras)
        self.save()

    def __str__(self):
        return f"Fatura de {self.usuario.username} - {self.mes}/{self.ano}"
