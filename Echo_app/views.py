from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

# Formulário de registro
class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "email", "password1", "password2"]

#Parte do Raul 
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

# Parte do Fialho 
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    user = request.user
    context = {
        "nome": user.first_name or user.username,
        "email": user.email,
    }
    return render(request, "dashboard.html", context)
