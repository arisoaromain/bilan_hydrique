from django.contrib import admin
from .models import Station, DonneesMensuelles, BilanHydro


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'latitude']


@admin.register(DonneesMensuelles)
class DonneesAdmin(admin.ModelAdmin):
    list_display = ['station', 'annee', 'mois', 'temperature_moy', 'precipitation']
    list_filter = ['station', 'annee']


@admin.register(BilanHydro)
class BilanAdmin(admin.ModelAdmin):
    list_display = ['station', 'methode', 'annee', 'mois', 'etp', 'etr', 'rfu', 'da']
    list_filter = ['station', 'methode', 'annee']
