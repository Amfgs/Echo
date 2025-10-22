# Echo/Echo_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
# Imports de formulários removidos
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import IntegrityError 

# Importe os modelos da sua aplicação
# ASSUMINDO que você tem um modelo Categoria em .models
from .models import Noticia, InteracaoNoticia, Notificacao, PerfilUsuario, Categoria

User = get_user_model()


# ===============================================
# Parte de Autenticação e Perfil (Raul)
# ===============================================

# Em Echo/Echo_app/views.py

def registrar(request):
    """
    Renderiza a página de registro e processa a criação de um novo usuário
    usando o NOME DE USUÁRIO fornecido no formulário.
    """
    contexto = {'erros': [], 'dados_preenchidos': {}} 
    
    try:
        contexto['todas_categorias'] = Categoria.objects.all()
    except:
        contexto['todas_categorias'] = []
    
    if request.method == "POST":
        # 2. Obter dados crus do POST
        username = request.POST.get('username') # <-- MUDANÇA: Lendo o username
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        categorias_selecionadas_ids = request.POST.getlist('categoria') 

        contexto['dados_preenchidos'] = {
            'username': username, # <-- MUDANÇA: Repassando o username
            'email': email,
            'categorias_selecionadas_ids': categorias_selecionadas_ids, 
        }

        # 3. Geração de Username REMOVIDA

        # 4. Validação manual
        if not username or not email or not password or not password_confirm: # <-- MUDANÇA
            contexto['erros'].append('Todos os campos obrigatórios devem ser preenchidos: Nome de Usuário, Email e Senha.')
        
        if password != password_confirm:
            contexto['erros'].append('As senhas não coincidem.')
        
        # A geração automática de username foi removida.
        # Agora, se o username já existe, apenas informamos o erro.
        if username and User.objects.filter(username__iexact=username).exists(): # <-- MUDANÇA
            contexto['erros'].append('Este nome de usuário já está em uso. Por favor, escolha outro.')
        
        if email and User.objects.filter(email__iexact=email).exists():
            contexto['erros'].append('Este e-mail já está cadastrado.')

        # 5. Se não houver erros, criar o usuário
        if not contexto['erros']:
            try:
                user = User.objects.create_user(
                    username=username, # <-- MUDANÇA: Usando o username do formulário
                    email=email,
                    password=password
                    # NOTA: O campo 'first_name' não está mais sendo salvo aqui.
                    # Se você quiser salvar o "Nome completo" também,
                    # precisará adicionar um novo campo no registrar.html
                )
                
                # 6. Salvar as categorias no PerfilUsuario
                if categorias_selecionadas_ids:
                    categorias = Categoria.objects.filter(pk__in=categorias_selecionadas_ids)
                    perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
                    perfil.categorias_de_interesse.set(categorias)
                
                # 7. Logar o usuário automaticamente
                login(request, user)
                return redirect("dashboard")
                
            except IntegrityError:
                contexto['erros'].append('Erro ao criar usuário. Tente novamente.')
            except Exception as e:
                contexto['erros'].append(f'Ocorreu um erro: {e}')

    return render(request, "Echo_app/registrar.html", contexto)


# === FUNÇÕES ADICIONADAS ===

# Em Echo/Echo_app/views.py

def entrar(request):
    """
    Renderiza a página de login e processa a autenticação do usuário
    usando USERNAME e SENHA (método padrão).
    """
    contexto = {}
    
    if request.method == "POST":
        # 1. Obter dados crus do POST (username e password)
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            contexto['erro_login'] = 'Por favor, preencha o usuário e a senha.'
            contexto['username_preenchido'] = username # Repassa o username
            return render(request, "Echo_app/entrar.html", contexto)

        # 2. Autenticar o usuário diretamente com username e senha
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 3. Sucesso!
            login(request, user)
            return redirect("dashboard")
        else:
            # 4. Falha na autenticação
            contexto['erro_login'] = 'Usuário ou senha inválidos. Tente novamente.'
        
        # Repassa o username digitado para preencher o campo
        contexto['username_preenchido'] = username
            
    # Se for GET ou se a autenticação falhar, renderiza a página
    return render(request, "Echo_app/entrar.html", contexto)


def sair(request):
    """
    Desloga o usuário e o redireciona para a página de login.
    """
    logout(request)
    return redirect("entrar")

# === FIM DAS FUNÇÕES ADICIONADAS ===


# ===============================================
# Parte do Dashboard (Fialho)
# ===============================================

@login_required
def dashboard(request):
    """
    Exibe a página principal para o usuário logado, incluindo
    notícias recomendadas e suas categorias de interesse.
    """
    user = request.user
    categorias_interesse = []

    # Tenta buscar o perfil do usuário e suas categorias de interesse
    try:
        # Usamos 'user.perfil' por causa do related_name="perfil" no OneToOneField
        perfil = user.perfil 
        categorias_interesse = perfil.categorias_de_interesse.all()
    except PerfilUsuario.DoesNotExist:
        # Se o perfil não existir por algum motivo, cria um
        perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
    
    # Monta o contexto para enviar ao template
    context = {
        "nome": user.first_name or user.username,
        "email": user.email, # Mantido conforme sua solicitação
        "noticias_recomendadas": Noticia.recomendar_para(user), # Corrigido o erro de digitação
        "categorias_interesse": categorias_interesse # <-- NOVO DADO ENVIADO
    }
    
    return render(request, "Echo_app/dashboard.html", context)


# ===============================================
# Parte de Notícias e Interações (Teteu)
# ===============================================

class NoticiaDetalheView(DetailView):
    """
    Exibe os detalhes de uma única notícia.
    """
    model = Noticia
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
        interacao.delete()
        acao_realizada = 'removida'
        status_interacao = False
    else:
        acao_realizada = 'adicionada'
        status_interacao = True
    
    if tipo_interacao == 'CURTIDA':
        noticia.curtidas_count = noticia.interacoes.filter(tipo='CURTIDA').count()
    elif tipo_interacao == 'SALVAMENTO':
        noticia.salvamentos_count = noticia.interacoes.filter(tipo='SALVAMENTO').count()
    noticia.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'acao': acao_realizada,
            'nova_contagem': getattr(noticia, f'{tipo_interacao.lower()}s_count'),
            'status_interacao': status_interacao,
            'tipo': tipo_interacao.lower()
        })
    
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
    return render(request, 'Echo_app/lista_notificacoes.html', context)

@login_required
@require_POST 
def marcar_notificacao_lida(request, notificacao_id):   
    """
    Marca uma notificação específica como lida.
    """
    notificacao = get_object_or_404(Notificacao, id=notificacao_id, usuario=request.user)
    notificacao.marcar_como_lida()
    return redirect('lista_notificações')

@login_required
@require_POST
def marcar_todas_lidas(request):
    """
    Marca todas as notificações não lidas do usuário como lidas.
    """
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return redirect('lista_notificacoes')