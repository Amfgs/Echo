from django.urls import path
from . import views 
from .views import NoticiaDetalheView

urlpatterns = [
    path("registrar/", views.registrar, name="registrar"),
    path("entrar/", views.entrar, name="entrar"),
    path("sair/", views.sair, name="sair"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path('noticia/<int:pk>/', NoticiaDetalheView.as_view(), name='noticia_detalhe'),
]
