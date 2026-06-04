"""
dgm_project/views.py
────────────────────
Vues communes aux deux modules :
  - login / logout / register
  - accueil_principal  (page de choix après connexion)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from agmet.models import Station as StationAgmet, Message
from bilan_hydro.models import Station as StationBilan, BilanHydro


# ══════════════════════════════════════════════════════════════
#  ACCUEIL PRINCIPAL (page de choix des modules)
# ══════════════════════════════════════════════════════════════

@login_required
def accueil_principal(request):
    """Page d'accueil commune — choix entre AGMET et Bilan Hydrique."""
    contexte = {
        # Stats AGMET
        'nb_stations_agmet':  StationAgmet.objects.count(),
        'nb_messages':        Message.objects.count(),
        'nb_messages_valides': Message.objects.filter(valide=True).count(),
        'derniers_messages':  Message.objects.order_by('-date_saisie')[:3],

        # Stats Bilan Hydrique
        'nb_stations_bilan':  StationBilan.objects.count(),
        'nb_bilans':          BilanHydro.objects.count(),
        'stations_bilan':     StationBilan.objects.all()[:5],
    }
    return render(request, 'accueil_principal.html', contexte)


# ══════════════════════════════════════════════════════════════
#  AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accueil_principal')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'accueil_principal')
            return redirect(next_url)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accueil_principal')

    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        errors = []
        if not username:
            errors.append("Le nom d'utilisateur est obligatoire.")
        elif User.objects.filter(username=username).exists():
            errors.append("Ce nom d'utilisateur est déjà pris.")
        if not password1:
            errors.append("Le mot de passe est obligatoire.")
        elif len(password1) < 6:
            errors.append("Le mot de passe doit contenir au moins 6 caractères.")
        elif password1 != password2:
            errors.append("Les deux mots de passe ne correspondent pas.")
        if email and User.objects.filter(email=email).exists():
            errors.append("Cette adresse e-mail est déjà utilisée.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            user = User.objects.create_user(
                username=username, password=password1,
                email=email, first_name=first_name, last_name=last_name,
            )
            login(request, user)
            messages.success(request,
                f"Bienvenue {first_name or username} ! Compte créé avec succès.")
            return redirect('accueil_principal')

    return render(request, 'register.html')
