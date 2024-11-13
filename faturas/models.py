from django.db import models
from django.contrib.auth.models import User
from datetime import datetime



class Compra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    produto = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    data_compra = models.DateTimeField(default=datetime.now)

    @property
    def total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.produto} - {self.usuario.username}"


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
