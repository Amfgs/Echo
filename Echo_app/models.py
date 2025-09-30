from django.db import models
from django.db import models
from django.contrib.auth import get_user_model # Recomendado para referenciar o modelo de Usuário
from django.utils import timezone

User = get_user_model()

class Noticia(models.Model):
    titulo = models.CharField(max_length=255, verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo Completo")
    data_publicacao = models.DateTimeField(default=timezone.now, verbose_name="Data de Publicação")
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias_criadas', verbose_name="Autor/Editor")

    curtidas_count = models.PositiveIntegerField(default=0, verbose_name="Total de Curtidas")
    salvamentos_count = models.PositiveIntegerField(default=0, verbose_name="Total de Salvamentos")

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data_publicacao'] 

    def __str__(self):
        return self.titulo

class InteracaoNoticia(models.Model):

    TIPO_INTERACAO_CHOICES = [
        ('CURTIDA', 'Curtida'),
        ('SALVAMENTO', 'Salvamento'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interacoes_noticias', verbose_name="Usuário")
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='interacoes', verbose_name="Notícia")
    tipo = models.CharField(max_length=10, choices=TIPO_INTERACAO_CHOICES, verbose_name="Tipo de Interação")
    data_interacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Interação")

    class Meta:
        verbose_name = "Interação de Notícia"
        verbose_name_plural = "Interações de Notícias"
        unique_together = ('usuario', 'noticia', 'tipo')

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} - {self.noticia.titulo}"

    @property
    def is_curtida(self):
        return self.tipo == 'CURTIDA'

    @property
    def is_salvamento(self):
        return self.tipo == 'SALVAMENTO'