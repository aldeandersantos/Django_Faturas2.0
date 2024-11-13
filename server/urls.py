from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('faturas.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
urlpatterns += [
    path('accounts/login/index.html', RedirectView.as_view(url='/')),
    path('login.html', RedirectView.as_view(url='/accounts/login/')),
    ]