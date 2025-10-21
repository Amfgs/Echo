from django.contrib import admin
# 1. Importe os outros modelos que você quer ver no admin
from .models import (
    PerfilUsuario, 
    Categoria, 
    Noticia, 
    InteracaoNoticia, 
    Notificacao
)

# 2. Sua configuração personalizada para PerfilUsuario (continua igual)
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "data_criacao")
    search_fields = ("usuario__username", "biografia")
    list_filter = ("data_criacao",)

# 3. Registre os outros modelos de forma simples
# (Você pode criar classes personalizadas para eles depois, se quiser)
admin.site.register(Categoria)
admin.site.register(Noticia)
admin.site.register(InteracaoNoticia)
admin.site.register(Notificacao)