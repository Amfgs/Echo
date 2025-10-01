from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "data_criacao")
    search_fields = ("usuario__username", "biografia")
    list_filter = ("data_criacao",)

