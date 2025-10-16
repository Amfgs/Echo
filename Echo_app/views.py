# Echo/Echo_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest

# Importe os modelos da sua aplicação
from .models import Noticia, InteracaoNoticia, Notificacao, PerfilUsuario

User = get_user_model()

# --- Formulários ---
# É uma boa prática manter os formulários em um arquivo separado (forms.py),
# mas para manter a simplicidade, deixaremos aqui por enquanto.

class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        # Adicionamos 'email' ao formulário de registro
        fields = ["username", "first_name", "email"]


# ===============================================
# Parte de Autenticação e Perfil (Raul)
# ===============================================

def registrar(request):
    """
    Renderiza a página de registro e processa a criação de um novo usuário.
    """
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Loga o usuário automaticamente após o registro
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistroForm()
    # ATUALIZADO: Caminho do template corrigido
    return render(request, "Echo_app/registrar.html", {"form": form})

def entrar(request):
    """
    Renderiza a página de login e processa a autenticação do usuário.
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redireciona para o dashboard após o login bem-sucedido
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    # ATUALIZADO: Caminho do template corrigido
    return render(request, "Echo_app/entrar.html", {"form": form})

def sair(request):
    """
    Desloga o usuário e o redireciona para a página de login.
    """
    logout(request)
    return redirect("entrar")

@login_required
def editar_perfil(request, nova_biografia=None, nova_foto=None):
    """
    Atualiza o perfil do usuário logado.
    (Nota: Esta view pode ser melhorada para usar um formulário e um template)
    """
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)
    if nova_biografia is not None:
        perfil.biografia = nova_biografia
    if nova_foto is not None:
        perfil.foto_perfil = nova_foto
    perfil.save()
    # O ideal seria redirecionar para uma página de perfil
    return redirect('dashboard')


# ===============================================
# Parte do Dashboard (Fialho)
# ===============================================

@login_required
def dashboard(request):
    """
    Exibe a página principal para o usuário logado.
    """
    user = request.user
    context = {
        "nome": user.first_name or user.username,
        "email": user.email,
        # Você pode adicionar aqui uma lista de notícias recomendadas
        "noticias_recomendadas": Noticia.recomendar_para(user)
    }
    # ATUALIZADO: Caminho do template corrigido
    return render(request, "Echo_app/dashboard.html", context)


# ===============================================
# Parte de Notícias e Interações (Teteu)
# ===============================================

class NoticiaDetalheView(DetailView):
    """
    Exibe os detalhes de uma única notícia.
    """
    model = Noticia
    # ATUALIZADO: Caminho do template corrigido
    template_name = 'Echo_app/noticia_detalhe.html'
    context_object_name = 'noticia'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        noticia = context['noticia']
        
        context['usuario_curtiu'] = False
        context['usuario_salvou'] = False

        if self.request.user.is_authenticated:
            usuario = self.request.user
            
            context['usuario_curtiu'] = InteracaoNoticia.objects.filter(
                usuario=usuario, noticia=noticia, tipo='CURTIDA'
            ).exists()
            
            context['usuario_salvou'] = InteracaoNoticia.objects.filter(
                usuario=usuario, noticia=noticia, tipo='SALVAMENTO'
            ).exists()

        return context

@login_required
@require_POST
def toggle_interacao(request, noticia_id, tipo_interacao):
    """
    Função genérica para adicionar ou remover uma interação (Curtida ou Salvamento).
    """
    if tipo_interacao not in ['CURTIDA', 'SALVAMENTO']:
        return HttpResponseBadRequest("Tipo de interação inválido.")

    noticia = get_object_or_404(Noticia, id=noticia_id)
    usuario = request.user
    
    interacao, created = InteracaoNoticia.objects.get_or_create(
        usuario=usuario,
        noticia=noticia,
        tipo=tipo_interacao
    )

    if not created:
        # Se a interação já existia, ela foi encontrada. Agora vamos deletá-la.
        interacao.delete()
        acao_realizada = 'removida'
        status_interacao = False
    else:
        # Se a interação não existia, ela foi criada.
        acao_realizada = 'adicionada'
        status_interacao = True
    
    # Atualiza a contagem no modelo da notícia
    if tipo_interacao == 'CURTIDA':
        noticia.curtidas_count = noticia.interacoes.filter(tipo='CURTIDA').count()
    elif tipo_interacao == 'SALVAMENTO':
        noticia.salvamentos_count = noticia.interacoes.filter(tipo='SALVAMENTO').count()
    noticia.save()

    # Responde com JSON se for uma requisição AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'acao': acao_realizada,
            'nova_contagem': getattr(noticia, f'{tipo_interacao.lower()}s_count'),
            'status_interacao': status_interacao,
            'tipo': tipo_interacao.lower()
        })
    
    # Redireciona de volta para a página anterior como fallback
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def curtir_noticia(request, noticia_id):
    """View de atalho para curtir uma notícia."""
    return toggle_interacao(request, noticia_id, 'CURTIDA')


@login_required
@require_POST
def salvar_noticia(request, noticia_id):
    """View de atalho para salvar uma notícia."""
    return toggle_interacao(request, noticia_id, 'SALVAMENTO')


# ===============================================
# Parte das Notificações (Oliver)
# ===============================================

@login_required
def lista_notificacoes(request):
    """
    Exibe a lista de notificações do usuário.
    """
    notificacoes = Notificacao.objects.filter(usuario=request.user)
    nao_lidas_count = notificacoes.filter(lida=False).count()
    
    context = {
        'notificacoes': notificacoes,
        'nao_lidas_count': nao_lidas_count
    }
    # ATUALIZADO: Caminho do template corrigido
    return render(request, 'Echo_app/lista_notificacoes.html', context)

@login_required
@require_POST 
def marcar_notificacao_lida(request, notificacao_id):   
    """
    Marca uma notificação específica como lida.
    """
    notificacao = get_object_or_404(Notificacao, id=notificacao_id, usuario=request.user)
    notificacao.marcar_como_lida()
    return redirect('lista_notificacoes')

@login_required
@require_POST
def marcar_todas_lidas(request):
    """
    Marca todas as notificações não lidas do usuário como lidas.
    """
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return redirect('lista_notificacoes')