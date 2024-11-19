from django.contrib import messages
from django.contrib.auth.models import User

def registra_usuario(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'As senhas não coincidem!')
            return request
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está registrado!')
            return request

        user = User.objects.create_user(
            username=email.split('@')[0],
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password1
        )
        user.save()
        messages.success(request, 'Usuário registrado com sucesso!')
        return None

    return request