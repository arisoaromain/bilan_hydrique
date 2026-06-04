from django.urls import path
from . import views

urlpatterns = [
    # Accueil module bilan
    path('', views.accueil, name='bilan_accueil'),

    # Import / stations
    path('import/',                          views.import_donnees,      name='import_donnees'),
    path('station/<int:station_id>/',        views.station_detail,      name='bilan_station_detail'),
    path('station/<int:station_id>/calcul/', views.calcul_bilan,        name='calcul_bilan'),
    path('station/<int:station_id>/historique/', views.historique,      name='historique'),
    path('station/<int:station_id>/supprimer/', views.supprimer_station,name='supprimer_station'),
    path('station/<int:station_id>/export/', views.export_excel,        name='export_excel'),

    # API JSON
    path('api/station/<int:station_id>/donnees/',
         views.api_donnees,        name='api_donnees'),
    path('api/station/<int:station_id>/comparaison/',
         views.api_comparaison_etp, name='api_comparaison_etp'),
]
