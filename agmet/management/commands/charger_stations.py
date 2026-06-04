"""
python manage.py charger_stations

Charge les stations météorologiques de Madagascar
listées dans le Tableau 8 du mémoire.
"""
from django.core.management.base import BaseCommand
from agmet.models import Station


STATIONS_MADAGASCAR = [
    # (identification, nom, type, longitude, latitude, altitude)
    ('22138', 'AMBOHITSILAOZANA',     '3',  48.45, 17.67, 780),
    ('32022', 'ANALAHAVA – AERO',     '1',  47.46, 14.38, 57),
    ('20555', 'ANDAPA',               '3',  49.37, 14.39, 474),
    ('21011', 'ANTALAHA',             '3',  50.27, 14.88, 6),
    ('32155', 'ANTANANARIVO – SCM',   '1',  47.82, 18.90, 1276),
    ('37022', 'ANTSIRABE – AERO',     '3',  47.02, 19.85, 500),
    ('10011', 'ANTSIRANANA – AERO',   '1',  49.28, 12.27, 100),
    ('32011', 'ANTSOHIHY',            '3',  47.99, 14.87, 92),
    ('67011', 'FARAFANGANA',          '3',  47.83, 22.82, 25),
    ('61641', 'FIANARANTSOA – AERO',  '1',  47.11, 21.44, 1109),
    ('67341', 'FORT DAUPHIN – AERO',  '1',  45.28, 25.03, 10),
    ('42033', 'MAHAJANGA – AERO',     '1',  46.35, 15.67, 8),
    ('49035', 'MAHANORO',             '3',  48.80, 19.90, 10),
    ('49511', 'MANANJARY – AERO',     '3',  48.37, 21.20, 20),
    ('43042', 'MANJA',                '3',  44.87, 21.42, 75),
    ('41022', 'MORONDAVA – AERO',     '3',  44.32, 20.28, 8),
    ('67561', 'SAINTE MARIE – AERO',  '3',  49.82, 17.10, 15),
    ('39011', 'TOAMASINA – AERO',     '1',  49.42, 18.10, 6),
    ('41032', 'TOLIARA – AERO',       '1',  43.72, 23.38, 10),
    ('42023', 'TSIROANOMANDIDY',      '3',  46.05, 18.78, 895),
    ('61822', 'IHOSY',                '3',  46.12, 22.40, 780),
    ('67063', 'VANGAINDRANO',         '3',  47.60, 23.35, 30),
]


class Command(BaseCommand):
    help = 'Charge les stations météorologiques de Madagascar (Tableau 8 du mémoire)'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for ident, nom, type_s, lon, lat, alt in STATIONS_MADAGASCAR:
            obj, created = Station.objects.update_or_create(
                identification=ident,
                defaults={
                    'nom': nom,
                    'type_station': type_s,
                    'longitude': lon,
                    'latitude': lat,
                    'altitude': alt,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Créée : {nom}'))
            else:
                updated_count += 1
                self.stdout.write(f'  ↻  Mise à jour : {nom}')

        self.stdout.write(self.style.SUCCESS(
            f'\n{created_count} station(s) créée(s), {updated_count} mise(s) à jour.'
        ))
