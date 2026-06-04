from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Authentification commune ──────────────────────────
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),
    path('register/', views.register_view, name='register'),

    # ── Page d'accueil commune (choix du module) ──────────
    path('', views.accueil_principal, name='accueil_principal'),

    # ── Module AGMET ──────────────────────────────────────
    path('agmet/', include('agmet.urls')),

    # ── Module Bilan Hydrique ─────────────────────────────
    path('bilan/', include('bilan_hydro.urls')),
]
