from django.urls import path
from . import views

urlpatterns = [
    # Accueil module AGMET
    path('', views.accueil, name='agmet_accueil'),

    # Stations
    path('stations/',                    views.station_liste,      name='station_liste'),
    path('stations/nouveau/',            views.station_creer,      name='station_creer'),
    path('stations/<int:pk>/',           views.station_detail,     name='station_detail'),
    path('stations/<int:pk>/modifier/',  views.station_modifier,   name='station_modifier'),
    path('stations/<int:pk>/supprimer/', views.station_supprimer,  name='station_supprimer'),

    # Messages AGMET
    path('messages/',                    views.message_liste,      name='message_liste'),
    path('messages/saisir/',             views.message_saisir,     name='message_saisir'),
    path('messages/<int:pk>/',           views.message_detail,     name='message_detail'),
    path('messages/<int:pk>/supprimer/', views.message_supprimer,  name='message_supprimer'),

    # Données dépouillées
    path('donnees/meteo/',               views.donnees_meteo_liste, name='donnees_meteo'),
    path('donnees/agro/',                views.donnees_agro_liste,  name='donnees_agro'),
    path('donnees/serie/',               views.serie_annuelle,      name='serie_annuelle'),

    # Bilan hydrique AGMET (simplifié)
    path('bilan-agmet/',                 views.bilan_hydrique,     name='bilan_hydrique'),

    # Export CSV
    path('export/meteo/',                views.export_csv_meteo,   name='export_meteo'),
    path('export/agro/',                 views.export_csv_agro,    name='export_agro'),
]
