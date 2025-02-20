import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



def user_directory_path(instance, filename):
    return os.path.join(instance.usuario.username, filename)

class UserFile(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    file_name = models.CharField(max_length=255, editable=False, default='arquivo')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    texto = models.TextField(max_length=2000, default='', blank=True)
    TIPO_CHOICES = [
        ('link', 'Link'),
        ('texto', 'Texto'),
        ('arquivo', 'Arquivo'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='arquivo', blank=False)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        if self.file and hasattr(self.file, 'name'):
            self.file_name = os.path.basename(self.file.name)
        
        super().save(*args, **kwargs)
        
        if is_new and self.file:
            self.file_name = os.path.basename(self.file.name)
            super().save(update_fields=['file_name'])
            
            UserActivity.objects.create(
                usuario=self.usuario,
                tipo='upload',
                descricao=f'Upload: {self.file_name}'
            )

    def delete(self, *args, **kwargs):
        file_name = os.path.basename(self.file.name) if self.file else self.file_name
        
        UserActivity.objects.create(
            usuario=self.usuario,
            tipo='delete',
            descricao=f'Deletou: {file_name}'
        )
        
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        if self.file:
            return f"{self.usuario.username} - {os.path.basename(self.file.name)}"
        return f"{self.usuario.username} - {self.file_name}"

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('upload', 'Upload'),
        ('delete', 'Delete'),
        ('compra', 'Compra')
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    descricao = models.CharField(max_length=255)
    data = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} - {self.descricao}"
