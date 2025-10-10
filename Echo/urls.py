from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Echo_app.urls')),  # ✅ conecta o app
]
