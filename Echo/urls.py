# Echo/Echo/urls.py

from django.contrib import admin
from django.urls import path, include
from Echo_app import views  # <-- 1. IMPORTE AS VIEWS DO SEU APP

urlpatterns = [
    path('admin/', admin.site.urls),

    # 2. DEFINA A ROTA RAIZ ('') PARA A VIEW DE LOGIN
    #    Quando alguém acessar "http://seu-site.com/", esta rota será usada.
    #    Estamos nomeando-a como 'entrar', que é o nome que já usamos nos templates.
    path('', views.entrar, name='entrar'), 
    
    # 3. MANTENHA AS OUTRAS ROTAS DO SEU APP EM UM "include"
    #    Isso é bom para organização. Todas as outras URLs (dashboard, registrar, etc.)
    #    serão gerenciadas pelo urls.py do Echo_app.
    path('app/', include('Echo_app.urls')),
]