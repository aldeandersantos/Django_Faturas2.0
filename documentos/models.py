import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User



def user_directory_path(instance, filename):
    return os.path.join(instance.usuario.username, filename)

class UserFile(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    texto = models.TextField(max_length=2000, default='', blank=True)
    TIPO_CHOICES = [
        ('link', 'Link'),
        ('texto', 'Texto'),
        ('arquivo', 'Arquivo'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='arquivo', blank=False)

    def __str__(self):
        return f"{self.usuario.username} - {self.file.name}"
