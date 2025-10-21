# /Users/godoy/Desktop/Echo/Echo/urls.py

from django.contrib import admin
from django.urls import path, include

# REMOVA ESTA LINHA: from Echo_app import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Esta linha faz todo o trabalho: delega todas as URLs do Echo_app
    # para a raiz (path='').
    path('', include('Echo_app.urls')),
]