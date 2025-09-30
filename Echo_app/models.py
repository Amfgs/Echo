from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# ===================== CLASSES TETEU =====================

class Noticia(models.Model):
    titulo = models.CharField(max_length=255, verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo Completo")
    data_publicacao = models.DateTimeField(default=timezone.now, verbose_name="Data de Publicação")
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias_criadas', verbose_name="Autor/Editor")
    
    curtidas_count = models.PositiveIntegerField(default=0, verbose_name="Total de Curtidas")
    salvamentos_count = models.PositiveIntegerField(default=0, verbose_name="Total de Salvamentos")
    
    # NOVO: categoria da notícia
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias', verbose_name="Categoria")
    
    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data_publicacao'] 

    def __str__(self):
        return self.titulo

    @staticmethod
    def recomendar_para(usuario):
        """
        Retorna queryset de notícias recomendadas para o usuário
        com base em preferências e histórico de interesse.
        """
        if not usuario.is_authenticated:
            return Noticia.objects.all()

        # Primeiro tenta pelas categorias preferidas
        prefs = getattr(usuario, 'preferencias', None)
        if prefs and prefs.categorias.exists():
            return Noticia.objects.filter(categoria__in=prefs.categorias.all())

        # Se não houver preferências, usa histórico de interesse
        historico = usuario.historico_interesse.order_by('-pontuacao')
        if historico.exists():
            top_categorias = [h.categoria for h in historico[:3]]  # top 3 categorias
            return Noticia.objects.filter(categoria__in=top_categorias)

        # fallback: mostra todas as notícias
        return Noticia.objects.all()


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


# ===================== CLASSES MOURY =====================

class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True, verbose_name="Categoria")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


class PreferenciaUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferencias", verbose_name="Usuário")
    categorias = models.ManyToManyField(Categoria, blank=True, related_name="usuarios_que_preferem", verbose_name="Categorias Preferidas")

    class Meta:
        verbose_name = "Preferência de Usuário"
        verbose_name_plural = "Preferências de Usuários"

    def __str__(self):
        return f"Preferências de {self.usuario.username}"


class HistoricoInteresse(models.Model):
    """
    Guarda pontuação de interesse do usuário em cada categoria
    com base no comportamento (curtidas, salvamentos, etc).
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="historico_interesse", verbose_name="Usuário")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="interesses", verbose_name="Categoria")
    pontuacao = models.PositiveIntegerField(default=0, verbose_name="Pontuação de Interesse")

    class Meta:
        verbose_name = "Histórico de Interesse"
        verbose_name_plural = "Históricos de Interesse"
        unique_together = ('usuario', 'categoria')

    def __str__(self):
        return f"{self.usuario.username} gosta de {self.categoria.nome}: {self.pontuacao} pontos"
    

# ===================== CLASSES OLIVEIRA =====================

class Notificacao(models.Model):
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        verbose_name="Usuário Destinatário"
    )

    manchete = models.CharField(
        max_length=255,
        verbose_name="Manchete/Conteúdo"
    )

    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificacoes',
        verbose_name="Notícia Relacionada"
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )

    lida = models.BooleanField(
        default=False,
        verbose_name="Lida"
    )

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-data_criacao', 'lida']

    def __str__(self):
        status = "[LIDA]" if self.lida else "[NOVA]"
        return f"{status} - Para {self.usuario.username}: {self.manchete}"

    def marcar_como_lida(self):
        if not self.lida:
            self.lida = True
            self.save()