# /Users/godoy/Desktop/Echo/Echo_app/urls.py

from django.urls import path
from . import views 
from .views import NoticiaDetalheView

urlpatterns = [
    path("", views.entrar, name="entrar"), 
    
    path("registrar/", views.registrar, name="registrar"),
    path("sair/", views.sair, name="sair"),
    path("dashboard/", views.dashboard, name="dashboard"),
    
    path('noticia/<int:pk>/', NoticiaDetalheView.as_view(), name='noticia_detalhe'),
    path('noticia/<int:noticia_id>/curtir/', views.curtir_noticia, name='noticia_curtir'),
    path('noticia/<int:noticia_id>/salvar/', views.salvar_noticia, name='noticia_salvar'),
]