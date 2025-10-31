# Echoproject/urls.py

from django.contrib import admin
from django.urls import path, include
# --- NOVOS IMPORTS ---
from django.conf import settings
from django.conf.urls.static import static
# --- FIM DOS NOVOS IMPORTS ---

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Delega as URLs do seu app para a raiz
    path('', include('Echo_app.urls')),
]

# --- BLOCO ADICIONADO ---
# Adiciona as URLs para servir ficheiros de media APENAS em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- FIM DO BLOCO ADICIONADO ---
