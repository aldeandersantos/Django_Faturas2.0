from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .forms import FileUploadForm
from .models import UserFile
from .utils import get_file_icon


@login_required
@require_http_methods(["GET", "POST"])
def gerenciar_arquivos(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user_file = form.save(commit=False)
            user_file.usuario = request.user
            user_file.save()
            if request.headers.get('HX-Request'):
                return HttpResponse("""
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        Arquivo enviado com sucesso!
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <script>
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    </script>
                """)
            messages.success(request, "Arquivo enviado com sucesso!")
            return redirect('documentos:gerenciar_arquivos')
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'documentos/form_upload.html', {'form': form})
            messages.error(request, "Erro ao enviar arquivo.")
            return redirect('documentos:gerenciar_arquivos')
    else:
        form = FileUploadForm()
        if request.headers.get('HX-Request'):
            return render(request, 'documentos/form_upload.html', {'form': form})
        
        arquivos = UserFile.objects.filter(
            usuario=request.user, 
            tipo='arquivo'
        ).order_by('-uploaded_at')
        
        for arquivo in arquivos:
            arquivo.icon = get_file_icon(arquivo.file.name)
        
        return render(request, 'documentos/gerenciar_arquivos.html', {
            'form': form,
            'arquivos': arquivos
        })


@login_required
@require_http_methods(["DELETE"])
def deletar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(UserFile, id=arquivo_id, usuario=request.user)
    try:
        arquivo.file.delete()
        arquivo.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, "Arquivo deletado com sucesso!")
    except Exception as e:
        if request.headers.get('HX-Request'):
            return HttpResponse(f"Erro ao deletar arquivo: {str(e)}", status=400)
        messages.error(request, f"Erro ao deletar arquivo: {str(e)}")
    
    return redirect('documentos:gerenciar_arquivos')