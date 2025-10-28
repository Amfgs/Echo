from django.db import models  # Importa classes base de modelos do Django
from django.contrib.auth import get_user_model  # Função para pegar o modelo de usuário configurado
from django.utils import timezone  # Para lidar com datas e horários
from django.db.models.signals import post_save  # Sinal executado após salvar um modelo
from django.dispatch import receiver  # Decorador que conecta funções aos sinais

User = get_user_model()  # Define o modelo de usuário usado no projeto


# ===================== CLASSES TETEU =====================

class Noticia(models.Model):  # Modelo que representa uma notícia
    titulo = models.CharField(max_length=255, verbose_name="Título")
    
    # --- CAMPO DE IMAGEM ADICIONADO ---
    imagem = models.ImageField(
        upload_to='noticias/',  # Subpasta dentro de MEDIA_ROOT onde as imagens serão salvas
        blank=True,             # Permite notícias sem imagem
        null=True,              # Permite valor nulo no banco de dados
        verbose_name="Imagem da Notícia"
    )
    # --- FIM DO CAMPO ADICIONADO ---
    
    conteudo = models.TextField(verbose_name="Conteúdo Completo")
    data_publicacao = models.DateTimeField(default=timezone.now, verbose_name="Data de Publicação")
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias_criadas', verbose_name="Autor/Editor")
    curtidas_count = models.PositiveIntegerField(default=0, verbose_name="Total de Curtidas")
    salvamentos_count = models.PositiveIntegerField(default=0, verbose_name="Total de Salvamentos")
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias', verbose_name="Categoria")

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo

    @staticmethod
    def recomendar_para(usuario):
        # ... (seu método recomendar_para continua igual) ...
        if not usuario.is_authenticated:
            return Noticia.objects.all()

        # Tenta buscar o perfil para preferências de categoria
        try:
            perfil = usuario.perfil # Usando related_name='perfil' de PerfilUsuario
            if perfil.categorias_de_interesse.exists():
                return Noticia.objects.filter(categoria__in=perfil.categorias_de_interesse.all()).order_by('-data_publicacao')[:10] # Limita a 10 por exemplo
        except AttributeError: # Caso o related_name não seja 'perfil' ou não exista PerfilUsuario
            pass
        except PerfilUsuario.DoesNotExist: # Caso o perfil ainda não exista
             pass

        # Fallback para histórico (se existir)
        # Note: HistoricoInteresse não está no código fornecido, assumindo que existe
        try:
            historico = usuario.historico_interesse.order_by('-pontuacao')
            if historico.exists():
                top_categorias = [h.categoria for h in historico[:3]]
                return Noticia.objects.filter(categoria__in=top_categorias).order_by('-data_publicacao')[:10]
        except AttributeError: # Se o related_name historico_interesse não existir
            pass

        # Fallback final: retorna as últimas notícias
        return Noticia.objects.all().order_by('-data_publicacao')[:10] # Retorna as 10 mais recentes


class InteracaoNoticia(models.Model):  # Modelo de interações (curtir/salvar)

    TIPO_INTERACAO_CHOICES = [
        ('CURTIDA', 'Curtida'),  # Tipo curtida
        ('SALVAMENTO', 'Salvamento'),  # Tipo salvamento
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interacoes_noticias', verbose_name="Usuário")  # Quem interagiu
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='interacoes', verbose_name="Notícia")  # Qual notícia
    tipo = models.CharField(max_length=10, choices=TIPO_INTERACAO_CHOICES, verbose_name="Tipo de Interação")  # Tipo da ação
    data_interacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Interação")  # Data da interação

    class Meta:
        verbose_name = "Interação de Notícia"
        verbose_name_plural = "Interações de Notícias"
        unique_together = ('usuario', 'noticia', 'tipo')  # Evita duplicatas

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} - {self.noticia.titulo}"  # Texto representativo

    @property
    def is_curtida(self):  # Retorna True se for curtida
        return self.tipo == 'CURTIDA'

    @property
    def is_salvamento(self):  # Retorna True se for salvamento
        return self.tipo == 'SALVAMENTO'


# ===================== CLASSES MOURY =====================

class Categoria(models.Model):  # Categoria de notícias
    nome = models.CharField(max_length=50, unique=True, verbose_name="Categoria")  # Nome único

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome  # Exibe o nome


class PreferenciaUsuario(models.Model):  # Preferências do usuário
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferencias", verbose_name="Usuário")  # Relaciona ao usuário
    categorias = models.ManyToManyField(Categoria, blank=True, related_name="usuarios_que_preferem", verbose_name="Categorias Preferidas")  # Categorias favoritas

    class Meta:
        verbose_name = "Preferência de Usuário"
        verbose_name_plural = "Preferências de Usuários"

    def __str__(self):
        return f"Preferências de {self.usuario.username}"  # Representação textual


class HistoricoInteresse(models.Model):  # Histórico de interesse do usuário

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="historico_interesse", verbose_name="Usuário")  # Usuário dono
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="interesses", verbose_name="Categoria")  # Categoria
    pontuacao = models.PositiveIntegerField(default=0, verbose_name="Pontuação de Interesse")  # Pontuação de interesse

    class Meta:
        verbose_name = "Histórico de Interesse"
        verbose_name_plural = "Históricos de Interesse"
        unique_together = ('usuario', 'categoria')  # Evita duplicação

    def __str__(self):
        return f"{self.usuario.username} gosta de {self.categoria.nome}: {self.pontuacao} pontos"  # Representação


# ===================== CLASSES OLIVEIRA =====================

class Notificacao(models.Model):  # Notificação enviada ao usuário

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        verbose_name="Usuário Destinatário"
    )  # Destinatário da notificação

    manchete = models.CharField(
        max_length=255,
        verbose_name="Manchete/Conteúdo"
    )  # Texto principal

    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificacoes',
        verbose_name="Notícia Relacionada"
    )  # Ligação com notícia (opcional)

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )  # Data de criação automática

    lida = models.BooleanField(
        default=False,
        verbose_name="Lida"
    )  # Status de leitura

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-data_criacao', 'lida']  # Ordena por data e leitura

    def __str__(self):
        status = "[LIDA]" if self.lida else "[NOVA]"  # Status da notificação
        return f"{status} - Para {self.usuario.username}: {self.manchete}"  # Representação textual

    def marcar_como_lida(self):
        if not self.lida:
            self.lida = True  # Marca como lida
            self.save()  # Salva alteração


# ===================== CLASSE RAUL =====================

class PerfilUsuario(models.Model):  # Perfil do usuário
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="Usuário"
    )  # Relaciona ao usuário
    biografia = models.TextField(
        verbose_name="Biografia",
        blank=True,
        null=True
    )  # Texto biográfico opcional
    foto_perfil = models.ImageField(
        upload_to="fotos_perfil/",
        blank=True,
        null=True,
        verbose_name="Foto de Perfil"
    )  # Foto do perfil
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )  # Data de criação automática

    # --- CAMPO ADICIONADO PARA CORRIGIR O ERRO ---
    categorias_de_interesse = models.ManyToManyField(
        Categoria,  # Liga este perfil a múltiplas Categorias
        blank=True, # Permite que um perfil seja criado sem nenhuma categoria
        related_name="perfis_interessados", # Nome da relação inversa
        verbose_name="Categorias de Interesse"
    )
    # --- FIM DO CAMPO ADICIONADO ---

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"
        ordering = ['-data_criacao']  # Ordena do mais recente

    def __str__(self):
        return f"Perfil de {self.usuario.username}"  # Representação textual


@receiver(post_save, sender=User)  # Cria perfil automaticamente ao criar usuário
def criar_perfil_automaticamente(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)  # Cria perfil