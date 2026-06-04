"""
Commande Django : python manage.py import_donnees <chemin_fichier.xlsx>
Importe les données horaires, agrège en mensuel, stocke en BD.
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from bilan_hydro.models import Station, DonneesMensuelles


class Command(BaseCommand):
    help = "Importe les données météo depuis un fichier Excel (.xlsx)"

    def add_arguments(self, parser):
        parser.add_argument('fichier', type=str, help="Chemin vers le fichier Excel")
        parser.add_argument('--station', type=str, default=None,
                            help="Nom de la station (défaut: détecté depuis le fichier)")
        parser.add_argument('--remplacement', action='store_true',
                            help="Remplacer les données existantes")

    def handle(self, *args, **options):
        fichier = options['fichier']
        if not os.path.exists(fichier):
            raise CommandError(f"Fichier introuvable : {fichier}")

        self.stdout.write(f"Lecture du fichier : {fichier}")

        # Lire le fichier
        try:
            raw = pd.read_excel(fichier, sheet_name=0, nrows=2, header=None)
            nom_station = str(raw.iloc[0, 1]).strip() if pd.notna(raw.iloc[0, 1]) else "Station"
            latitude_val = float(raw.iloc[0, 1]) if str(raw.iloc[0, 1]).replace('-', '').replace('.', '').isdigit() else -18.9

            # Récupérer la latitude depuis la ligne 0, col 1
            try:
                latitude_val = float(raw.iloc[0, 1])
                nom_station = options.get('station') or "Betafo"
            except (ValueError, TypeError):
                nom_station = str(raw.iloc[0, 1]).strip()
                latitude_val = -18.9

            # Lire les données avec les bonnes colonnes
            df = pd.read_excel(fichier, skiprows=2, header=0)
            df.columns = ['Date', 'Temperature', 'Precipitation', 'Humidite', 'Insolation']
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])

            # Forcer types numériques
            for col in ['Temperature', 'Precipitation', 'Humidite', 'Insolation']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        except Exception as e:
            raise CommandError(f"Erreur lecture fichier : {e}")

        self.stdout.write(f"  Station : {nom_station}, Latitude : {latitude_val}")
        self.stdout.write(f"  Données : {len(df)} lignes ({df['Date'].min().year}-{df['Date'].max().year})")

        # Agrégation mensuelle
        df['annee'] = df['Date'].dt.year
        df['mois'] = df['Date'].dt.month
        monthly = df.groupby(['annee', 'mois']).agg(
            temperature_moy=('Temperature', 'mean'),
            precipitation=('Precipitation', 'sum'),
            humidite_moy=('Humidite', 'mean'),
            insolation=('Insolation', 'sum')
        ).reset_index()

        # Créer ou récupérer la station
        station, created = Station.objects.get_or_create(
            nom=nom_station,
            defaults={'latitude': latitude_val}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  Station créée : {nom_station}"))
        else:
            self.stdout.write(f"  Station existante : {nom_station}")

        # Insérer les données mensuelles
        compteur = 0
        for _, row in monthly.iterrows():
            obj, created = DonneesMensuelles.objects.update_or_create(
                station=station,
                annee=int(row['annee']),
                mois=int(row['mois']),
                defaults={
                    'temperature_moy': round(float(row['temperature_moy']), 4),
                    'precipitation': round(float(row['precipitation']), 4),
                    'humidite_moy': round(float(row['humidite_moy']), 4),
                    'insolation': round(float(row['insolation']), 4),
                }
            )
            if created:
                compteur += 1

        self.stdout.write(self.style.SUCCESS(
            f"  {compteur} enregistrements créés / {len(monthly)} total importés."
        ))
