from django.contrib import admin
from .models import Station, Message, DonneesMeteo, DonneesAgro, SerieAnnuelle


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display  = ['identification', 'nom', 'type_station', 'latitude', 'longitude', 'altitude']
    search_fields = ['identification', 'nom']
    list_filter   = ['type_station']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display    = ['identification', 'nom', 'annee', 'mois', 'decade', 'valide', 'date_saisie']
    list_filter     = ['valide', 'mois', 'decade']
    search_fields   = ['identification', 'nom']
    ordering        = ['-annee', '-mois', '-decade']
    readonly_fields = ['date_saisie']


@admin.register(DonneesMeteo)
class DonneesMeteoAdmin(admin.ModelAdmin):
    list_display  = ['identification', 'nom', 'annee', 'mois', 'decade',
                     'tn', 'tx', 'un', 'ux', 'rrr', 'id_insol', 'ev']
    list_filter   = ['mois', 'decade']
    search_fields = ['identification', 'nom']
    fieldsets = [
        ('Identification', {
            'fields': ['message', 'identification', 'nom', 'annee', 'mois', 'decade',
                       'longitude', 'latitude', 'altitude']
        }),
        ('2ème section (666) — Vent & Températures', {
            'fields': ['fff', 'fdfdfd', 'tn', 'tx', 'un', 'ux']
        }),
        ('3ème section (777) — Précipitations', {
            'fields': ['n', 'rrr']
        }),
        ('4ème section (888) — Insolation · Évaporation · Sol', {
            'fields': ['id_insol', 'ev', 'tng']
        }),
        ('Contrôle qualité', {
            'fields': ['erreurs'],
            'classes': ['collapse'],
        }),
    ]


@admin.register(DonneesAgro)
class DonneesAgroAdmin(admin.ModelAdmin):
    list_display  = ['identification', 'nom', 'annee', 'mois', 'decade',
                     'nom_secva', 'culture1', 'culture2', 'culture3']
    list_filter   = ['mois', 'decade']
    search_fields = ['identification', 'nom', 'culture1', 'nom_secva']
    fieldsets = [
        ('Identification', {
            'fields': ['message', 'identification', 'nom', 'annee', 'mois', 'decade',
                       'nom_secva', 'longitude', 'latitude', 'altitude']
        }),
        ('Culture 1  —  11C₁C₁F₁  /  22E₁S₁A₁', {
            'fields': ['culture1', 'code_cult1', 'phenologie1', 'ennemis1', 'degat1', 'aspect1']
        }),
        ('Culture 2  —  33C₂C₂F₂  /  44E₂S₂A₂', {
            'fields': ['culture2', 'code_cult2', 'phenologie2', 'ennemis2', 'degat2', 'aspect2'],
            'classes': ['collapse'],
        }),
        ('Culture 3  —  55C₃C₃F₃  /  66E₃S₃A₃', {
            'fields': ['culture3', 'code_cult3', 'phenologie3', 'ennemis3', 'degat3', 'aspect3'],
            'classes': ['collapse'],
        }),
    ]


@admin.register(SerieAnnuelle)
class SerieAnnuelleAdmin(admin.ModelAdmin):
    list_display  = ['station', 'parametre', 'annee']
    list_filter   = ['parametre', 'annee']
    search_fields = ['station__nom', 'station__identification']
