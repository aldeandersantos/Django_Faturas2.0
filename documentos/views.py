from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FileUploadForm
from .models import UserFile



@login_required
def upload_arquivo(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user_file = form.save(commit=False)
            user_file.usuario = request.user
            user_file.save()
            messages.success(request, "Arquivo enviado com sucesso!")
            return render(request, 'documentos/upload.html', {'form': form})
    else:
        form = FileUploadForm()
    
    return render(request, 'documentos/upload.html', {'form': form})


@login_required
def listar_arquivos(request):
    arquivos = UserFile.objects.filter(usuario=request.user, tipo='arquivo')
    
    return render(request, 'documentos/listar_arquivos.html', {'arquivos': arquivos})