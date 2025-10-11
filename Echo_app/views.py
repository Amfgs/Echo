from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest

# Importe os modelos da sua aplicação de notícias
from .models import Noticia, InteracaoNoticia

User = get_user_model()

# Formulário de registro
class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "email"]  # UserCreationForm já trata password1 e password2

# Parte de Autenticação (Raul)
def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistroForm()
    return render(request, "registrar.html", {"form": form})

def entrar(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "entrar.html", {"form": form})

def sair(request):
    logout(request)
    return redirect("entrar")

# Parte do Dashboard (Fialho)
@login_required
def dashboard(request):
    user = request.user
    print(f"[DEBUG] Usuário acessando dashboard: {user.username}")  # <<< linha adicionada para debug rápido
    context = {
        "nome": user.first_name or user.username,
        "email": user.email,
    }
    return render(request, "dashboard.html", context)

# Parte de Notícias (Teteu)

class NoticiaDetalheView(DetailView):
    model = Noticia
    template_name = 'seuapp/noticia_detalhe.html'
    context_object_name = 'noticia'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        noticia = context['noticia']
        
        context['usuario_curtiu'] = False
        context['usuario_salvou'] = False

        if self.request.user.is_authenticated:
            usuario = self.request.user
            
            curtida_existente = InteracaoNoticia.objects.filter(
                usuario=usuario, 
                noticia=noticia, 
                tipo='CURTIDA'
            ).exists()
            context['usuario_curtiu'] = curtida_existente
            
            salvamento_existente = InteracaoNoticia.objects.filter(
                usuario=usuario, 
                noticia=noticia, 
                tipo='SALVAMENTO'
            ).exists()
            context['usuario_salvou'] = salvamento_existente

        return context

@login_required
@require_POST
def toggle_interacao(request, noticia_id, tipo_interacao):
    if tipo_interacao not in ['CURTIDA', 'SALVAMENTO']:
        return HttpResponseBadRequest("Tipo de interação inválido.")

    noticia = get_object_or_404(Noticia, id=noticia_id)
    usuario = request.user
    
    try:
        interacao = InteracaoNoticia.objects.get(
            usuario=usuario,
            noticia=noticia,
            tipo=tipo_interacao
        )
        
        interacao.delete()
        acao_realizada = 'removida'
        nova_contagem = InteracaoNoticia.objects.filter(noticia=noticia, tipo=tipo_interacao).count()
        status_interacao = False

    except InteracaoNoticia.DoesNotExist:
        InteracaoNoticia.objects.create(
            usuario=usuario,
            noticia=noticia,
            tipo=tipo_interacao
        )
        acao_realizada = 'adicionada'
        nova_contagem = InteracaoNoticia.objects.filter(noticia=noticia, tipo=tipo_interacao).count()
        status_interacao = True

    if tipo_interacao == 'CURTIDA':
        noticia.curtidas_count = nova_contagem
    elif tipo_interacao == 'SALVAMENTO':
        noticia.salvamentos_count = nova_contagem
    noticia.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'acao': acao_realizada,
            'nova_contagem': nova_contagem,
            'status_interacao': status_interacao,
            'tipo': tipo_interacao.lower()
        })
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def curtir_noticia(request, noticia_id):
    return toggle_interacao(request, noticia_id, 'CURTIDA')

@login_required
@require_POST
def salvar_noticia(request, noticia_id):
    return toggle_interacao(request, noticia_id, 'SALVAMENTO')
