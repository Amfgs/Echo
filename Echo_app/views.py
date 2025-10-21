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

def registrar(request):
    """
    Renderiza a página de registro e processa a criação de um novo usuário
    SEM usar Django Forms, mapeando os campos da imagem (Nome, Email, Senha, Categorias).
    """
    # Adicionado 'dados_preenchidos' para repassar ao template em caso de erro
    contexto = {'erros': [], 'dados_preenchidos': {}} 
    
    # 1. Busca todas as categorias para exibir no template (GET e POST com erro)
    try:
        contexto['todas_categorias'] = Categoria.objects.all()
    except:
        contexto['todas_categorias'] = []
    
    if request.method == "POST":
        # 2. Obter dados crus do POST (mapeando para os campos da imagem)
        nome_completo = request.POST.get('nome_completo') # <--- Campo 'Nome completo' da imagem
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        # Obter categorias selecionadas (lista de valores do checkbox/input)
        categorias_selecionadas_ids = request.POST.getlist('categoria') 

        # Repassa os dados para repreencher o formulário em caso de erro
        contexto['dados_preenchidos'] = {
            'nome_completo': nome_completo,
            'email': email,
            # Mantém os IDs das categorias para re-checar os checkboxes
            'categorias_selecionadas_ids': categorias_selecionadas_ids, 
        }

        # 3. Geração de Username (necessário pelo User padrão do Django)
        # Usa a parte do email antes do '@' como base
        username_base = email.split('@')[0].replace('.', '_').replace('-', '_') if email and '@' in email else None
        username = username_base
        
        # 4. Validação manual
        if not nome_completo or not email or not password or not password_confirm:
            contexto['erros'].append('Todos os campos obrigatórios devem ser preenchidos: Nome completo, Email e Senha.')
        
        if password != password_confirm:
            contexto['erros'].append('As senhas não coincidem.')
        
        if not username:
             contexto['erros'].append('E-mail inválido.')
        
        # Verifica se o username gerado já está em uso, gerando um novo se necessário
        counter = 1
        while username and User.objects.filter(username=username).exists():
            username = f"{username_base}_{counter}"
            counter += 1
        
        if email and User.objects.filter(email=email).exists():
            contexto['erros'].append('Este e-mail já está cadastrado.')

        # 5. Se não houver erros, criar o usuário
        if not contexto['erros']:
            try:
                user = User.objects.create_user(
                    # Usa o username gerado/ajustado
                    username=username, 
                    email=email,
                    password=password,
                    # Usa o "Nome completo" como first_name
                    first_name=nome_completo 
                )
                
                # 6. Salvar as categorias no PerfilUsuario
                if categorias_selecionadas_ids:
                    # Busca as categorias pelos IDs (PKs)
                    categorias = Categoria.objects.filter(pk__in=categorias_selecionadas_ids)
                    
                    # Assume que o PerfilUsuario é criado automaticamente ou que 
                    # get_or_create garantirá sua existência.
                    perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)

                    # ASSUMINDO que PerfilUsuario tem um campo:
                    # categorias_de_interesse = models.ManyToManyField(Categoria, ...)
                    perfil.categorias_de_interesse.set(categorias)
                
                # 7. Logar o usuário automaticamente
                login(request, user)
                return redirect("dashboard")
                
            except IntegrityError:
                # Segurança extra
                contexto['erros'].append('Erro ao criar usuário. Tente novamente.')
                if 'user' in locals() and not user.pk: # Tenta deletar se criado e sem PK
                     pass # Não se preocupa em deletar, o erro já deve ter impedido a criação.
            except Exception as e:
                # Captura outros erros inesperados
                contexto['erros'].append(f'Ocorreu um erro: {e}')

    # Se for GET ou se houver erros no POST, renderiza a página com o contexto
    return render(request, "Echo_app/registrar.html", contexto)


# === FUNÇÕES ADICIONADAS ===

def entrar(request):
    """
    Renderiza a página de login e processa a autenticação do usuário
    SEM usar Django Forms.
    """
    contexto = {}
    
    if request.method == "POST":
        # 1. Obter dados crus do POST
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            contexto['erro_login'] = 'Por favor, preencha o usuário e a senha.'
            return render(request, "Echo_app/entrar.html", contexto)

        # 2. Autenticar o usuário
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 3. Se a autenticação for bem-sucedida, logar
            login(request, user)
            return redirect("dashboard")
        else:
            # 4. Se a autenticação falhar, enviar erro
            contexto['erro_login'] = 'Usuário ou senha inválidos. Tente novamente.'
            # Também é bom repassar o username para preencher o formulário novamente
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
    Exibe a página principal para o usuário logado.
    """
    user = request.user
    context = {
        "nome": user.first_name or user.username,
        "email": user.email,
        "noticias_recomendADAS": Noticia.recomendar_para(user)
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