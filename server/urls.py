from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('faturas.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

def custom_404(request, exception):
    return render(request, 'faturas/404.html', status=404)

handler404 = custom_404