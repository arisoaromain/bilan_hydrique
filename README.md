# DGM Madagascar — Portail Agro-Météorologie

Fusion de deux modules Django en un seul portail :
- **Module AGMET** : dépouillement des messages agro-météorologiques décadaires
- **Module Bilan Hydrique** : calcul ETP/ETR/RFU par Thornthwaite et Turc

## Installation

```bash
pip install django pandas openpyxl
cd dgm_project
python manage.py migrate
python manage.py charger_stations      # Stations AGMET de Madagascar
python manage.py createsuperuser       # Compte administrateur
python manage.py runserver
```

Ouvrez : http://127.0.0.1:8000/

## Navigation

1. **Login** → page d'authentification commune
2. **Portail** → choix entre AGMET et Bilan Hydrique
3. Bouton **Portail** dans chaque module pour revenir à l'accueil commun
