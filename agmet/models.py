from django.db import models


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : station
# Tableau 10 du mémoire – dictionnaire des données de la table « station »
# ─────────────────────────────────────────────────────────────────────────────
class Station(models.Model):
    """Stations météorologiques à Madagascar."""

    TYPE_CHOICES = [
        ('1', 'Station synoptique (OMM)'),
        ('2', 'Station agro-météorologique'),
        ('3', 'Station climatologique principale'),
        ('4', 'Station climatologique ordinaire'),
        ('5', 'Poste pluviométrique'),
        ('6', 'Poste pluviométrique et agro-météorologique'),
        ('9', 'Type indéterminé'),
    ]

    identification = models.CharField(
        max_length=5,
        unique=True,
        verbose_name="Indicatif mécanographique",
        help_text="Code unique de 5 chiffres (ex: 32155)"
    )
    nom = models.CharField(max_length=100, verbose_name="Nom de la station")
    type_station = models.CharField(
        max_length=1,
        choices=TYPE_CHOICES,
        default='2',
        verbose_name="Type de station"
    )
    longitude = models.FloatField(verbose_name="Longitude (°E)")
    latitude = models.FloatField(verbose_name="Latitude (°S, valeur positive)")
    altitude = models.FloatField(null=True, blank=True, verbose_name="Altitude (m)")

    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        ordering = ['nom']

    def __str__(self):
        return f"{self.identification} – {self.nom}"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : message
# Tableau 11 – stockage brut du message AGMET reçu
# ─────────────────────────────────────────────────────────────────────────────
class Message(models.Model):
    """Message AGMET complet, tel que transmis par la station."""

    DECADE_CHOICES = [
        ('51', '1ère décade (1–10)'),
        ('52', '2ème décade (11–20)'),
        ('53', '3ème décade (21–fin)'),
    ]
    MOIS_CHOICES = [
        ('01', 'Janvier'), ('02', 'Février'), ('03', 'Mars'),
        ('04', 'Avril'),   ('05', 'Mai'),     ('06', 'Juin'),
        ('07', 'Juillet'), ('08', 'Août'),    ('09', 'Septembre'),
        ('10', 'Octobre'), ('11', 'Novembre'),('12', 'Décembre'),
    ]

    station = models.ForeignKey(
        Station, on_delete=models.CASCADE,
        related_name='messages', null=True, blank=True
    )
    identification = models.CharField(
        max_length=5, verbose_name="Indicatif mécanographique"
    )
    nom = models.CharField(
        max_length=100, blank=True, verbose_name="Nom de la station"
    )
    longitude = models.FloatField(null=True, blank=True)
    latitude  = models.FloatField(null=True, blank=True)
    altitude  = models.FloatField(null=True, blank=True)
    annee     = models.IntegerField(verbose_name="Année")
    mois      = models.CharField(max_length=2, choices=MOIS_CHOICES, verbose_name="Mois")
    decade    = models.CharField(max_length=2, choices=DECADE_CHOICES, verbose_name="Décade")
    message_brut = models.TextField(verbose_name="Message AGMET brut")
    date_saisie  = models.DateTimeField(auto_now_add=True)
    valide       = models.BooleanField(default=False, verbose_name="Validé (aucune erreur)")

    class Meta:
        verbose_name = "Message AGMET"
        verbose_name_plural = "Messages AGMET"
        ordering = ['-annee', '-mois', '-decade']
        unique_together = ('identification', 'annee', 'mois', 'decade')

    def __str__(self):
        return f"AGMET {self.identification} – {self.annee}/{self.mois} Décade {self.decade}"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : données (météo décadaires dépouillées)
# Tableau 12 – paramètres météorologiques extraits du message
# ─────────────────────────────────────────────────────────────────────────────
class DonneesMeteo(models.Model):
    """Paramètres météorologiques décadaires dépouillés du message AGMET."""

    message = models.OneToOneField(
        Message, on_delete=models.CASCADE,
        related_name='donnees_meteo', null=True, blank=True
    )
    identification = models.CharField(max_length=5)
    nom            = models.CharField(max_length=100, blank=True)
    longitude      = models.FloatField(null=True, blank=True)
    latitude       = models.FloatField(null=True, blank=True)
    altitude       = models.FloatField(null=True, blank=True)
    annee          = models.IntegerField()
    mois           = models.CharField(max_length=2)
    decade         = models.CharField(max_length=2)

    # Vent moyen (Omfff)
    fff = models.FloatField(
        null=True, blank=True,
        verbose_name="Vent moyen total (fff)",
        help_text="Force totale du vent moyen sur la décade"
    )
    # Vent diurne (1mfdfdfd)
    fdfdfd = models.FloatField(
        null=True, blank=True,
        verbose_name="Vent diurne total (fdfdfd)"
    )
    # Températures (4SnTnTnTn et 6SnTxTxTx)
    tn = models.FloatField(
        null=True, blank=True,
        verbose_name="Tmin moyenne décade (°C)"
    )
    tx = models.FloatField(
        null=True, blank=True,
        verbose_name="Tmax moyenne décade (°C)"
    )
    # Humidité (8UnUnUxUx)
    un = models.IntegerField(
        null=True, blank=True,
        verbose_name="Humidité relative min moyenne (%)"
    )
    ux = models.IntegerField(
        null=True, blank=True,
        verbose_name="Humidité relative max moyenne (%)"
    )
    # Pluie (7777 1qann 2RRRr)
    n   = models.IntegerField(null=True, blank=True, verbose_name="Nombre de jours avec pluie")
    rrr = models.FloatField(null=True, blank=True, verbose_name="Précipitation décadaire (mm)")
    # Insolation (0IdIdIdId)
    id_insol = models.FloatField(
        null=True, blank=True,
        verbose_name="Insolation totale (heures)"
    )
    # Évaporation (1MEvEvEv)
    ev = models.FloatField(
        null=True, blank=True,
        verbose_name="Évaporation totale (mm)"
    )
    # Température sol (2SnTngTngTng)
    tng = models.FloatField(
        null=True, blank=True,
        verbose_name="Tmin sol 10 cm moyenne (°C)"
    )

    # Erreurs détectées lors du dépouillement
    erreurs = models.TextField(blank=True, default='', verbose_name="Erreurs détectées")

    class Meta:
        verbose_name = "Données météo"
        verbose_name_plural = "Données météo"
        ordering = ['-annee', '-mois', '-decade']

    def __str__(self):
        return f"Données {self.identification} – {self.annee}/{self.mois} D{self.decade}"

    @property
    def tm(self):
        """Température moyenne = (Tmin + Tmax) / 2"""
        if self.tn is not None and self.tx is not None:
            return round((self.tn + self.tx) / 2, 1)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : donnéesAgro  (données agricoles dépouillées)
# Tableau 13 – suivi agro-météorologique des cultures (3 cultures max)
# ─────────────────────────────────────────────────────────────────────────────
class DonneesAgro(models.Model):
    """
    Données agrométéorologiques – Section 5 du message AGMET.

    Structure du mémoire (II.2.1) :
      Nom_SECVA  999
      11C₁C₁F₁  22E₁S₁A₁
      33C₂C₂F₂  44E₂S₂A₂
      55C₃C₃F₃  66E₃S₃A₃
      FIN MESSAGE

    CcCc = code culture (01=Riz, 02=Maïs…)
    F    = phénologie (0–9)
    E    = ennemis (0–9)
    S    = dégâts / severity (0–4)
    A    = aspect général (1–5)
    """

    PHENOLOGIE_CHOICES = [
        ('0', 'Pas observable'),
        ('1', 'Semis / plantation'),
        ('2', 'Levée / germination'),
        ('3', 'Tallage / développement végétatif'),
        ('4', 'Montaison / épiaison'),
        ('5', 'Floraison'),
        ('6', 'Fructification / remplissage'),
        ('7', 'Maturation'),
        ('8', 'Récolte'),
        ('9', 'Jachère'),
    ]
    ENNEMIS_CHOICES = [
        ('0', 'Aucun'),
        ('1', 'Insectes'),
        ('2', 'Maladies fongiques'),
        ('3', 'Maladies virales'),
        ('4', 'Mauvaises herbes'),
        ('5', 'Oiseaux'),
        ('6', 'Rongeurs'),
        ('7', 'Sécheresse'),
        ('8', "Excès d'eau"),
        ('9', 'Autre'),
    ]
    DEGAT_CHOICES = [
        ('0', 'Aucun dégât'),
        ('1', 'Dégâts légers'),
        ('2', 'Dégâts modérés'),
        ('3', 'Dégâts graves'),
        ('4', 'Perte totale'),
    ]
    ASPECT_CHOICES = [
        ('1', 'Très bon'),
        ('2', 'Bon'),
        ('3', 'Moyen'),
        ('4', 'Mauvais'),
        ('5', 'Très mauvais'),
    ]

    message = models.OneToOneField(
        Message, on_delete=models.CASCADE,
        related_name='donnees_agro', null=True, blank=True
    )
    identification = models.CharField(max_length=5)
    nom            = models.CharField(max_length=100, blank=True)
    longitude      = models.FloatField(null=True, blank=True)
    latitude       = models.FloatField(null=True, blank=True)
    altitude       = models.FloatField(null=True, blank=True)
    annee          = models.IntegerField()
    mois           = models.CharField(max_length=2)
    decade         = models.CharField(max_length=2)

    # Nom de la SECVA (poste agrométéorologique)
    nom_secva = models.CharField(max_length=100, blank=True, verbose_name="Nom SECVA")

    # ── Culture 1 : groupes 11CcCcF  22ESA ───────────────────────────────────
    culture1      = models.CharField(max_length=100, blank=True, verbose_name="Culture 1")
    code_cult1    = models.CharField(max_length=2,   blank=True, verbose_name="Code culture 1")
    phenologie1   = models.CharField(max_length=1, choices=PHENOLOGIE_CHOICES, blank=True,
                                     verbose_name="Phénologie C1 (F)")
    ennemis1      = models.CharField(max_length=1, choices=ENNEMIS_CHOICES, blank=True,
                                     verbose_name="Ennemis C1 (E)")
    degat1        = models.CharField(max_length=1, choices=DEGAT_CHOICES, blank=True,
                                     verbose_name="Dégâts C1 (S)")
    aspect1       = models.CharField(max_length=1, choices=ASPECT_CHOICES, blank=True,
                                     verbose_name="Aspect C1 (A)")

    # ── Culture 2 : groupes 33CcCcF  44ESA ───────────────────────────────────
    culture2      = models.CharField(max_length=100, blank=True, verbose_name="Culture 2")
    code_cult2    = models.CharField(max_length=2,   blank=True)
    phenologie2   = models.CharField(max_length=1, choices=PHENOLOGIE_CHOICES, blank=True,
                                     verbose_name="Phénologie C2 (F)")
    ennemis2      = models.CharField(max_length=1, choices=ENNEMIS_CHOICES, blank=True,
                                     verbose_name="Ennemis C2 (E)")
    degat2        = models.CharField(max_length=1, choices=DEGAT_CHOICES, blank=True,
                                     verbose_name="Dégâts C2 (S)")
    aspect2       = models.CharField(max_length=1, choices=ASPECT_CHOICES, blank=True,
                                     verbose_name="Aspect C2 (A)")

    # ── Culture 3 : groupes 55CcCcF  66ESA ───────────────────────────────────
    culture3      = models.CharField(max_length=100, blank=True, verbose_name="Culture 3")
    code_cult3    = models.CharField(max_length=2,   blank=True)
    phenologie3   = models.CharField(max_length=1, choices=PHENOLOGIE_CHOICES, blank=True,
                                     verbose_name="Phénologie C3 (F)")
    ennemis3      = models.CharField(max_length=1, choices=ENNEMIS_CHOICES, blank=True,
                                     verbose_name="Ennemis C3 (E)")
    degat3        = models.CharField(max_length=1, choices=DEGAT_CHOICES, blank=True,
                                     verbose_name="Dégâts C3 (S)")
    aspect3       = models.CharField(max_length=1, choices=ASPECT_CHOICES, blank=True,
                                     verbose_name="Aspect C3 (A)")

    class Meta:
        verbose_name = "Données agro"
        verbose_name_plural = "Données agro"

    def __str__(self):
        cultures = ', '.join(filter(None, [self.culture1, self.culture2, self.culture3]))
        return f"Agro {self.identification} – {self.annee}/{self.mois} D{self.decade} [{cultures}]"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : pluie annuelle (et toutes les séries décadaires annuelles)
# Tableau 14 – une ligne par station/année, 36 colonnes (3 décades × 12 mois)
# La même structure sert pour : fff, fdfdfd, Tn, Tx, Un, Ux, RRR,
#   insolation, évaporation, Tng  → on utilise un champ "parametre"
# ─────────────────────────────────────────────────────────────────────────────
PARAMETRES = [
    ('RRR',    'Précipitation (mm)'),
    ('fff',    'Vent total (m/s ou km)'),
    ('fdfdfd', 'Vent diurne'),
    ('Tn',     'Température min (°C)'),
    ('Tx',     'Température max (°C)'),
    ('Un',     'Humidité min (%)'),
    ('Ux',     'Humidité max (%)'),
    ('Id',     'Insolation (h)'),
    ('Ev',     'Évaporation (mm)'),
    ('Tng',    'T° sol 10 cm (°C)'),
]

MOIS_ABBR = ['Janv', 'Fev', 'Mars', 'Avr', 'Mai', 'Juin',
             'Jul', 'Aout', 'Sept', 'Oct', 'Nov', 'Dec']


def _build_decade_fields():
    """Génère les 36 champs décadaires (1Janv … 3Dec)."""
    fields = {}
    for m in MOIS_ABBR:
        for d in range(1, 4):
            fname = f"d{d}{m}"
            fields[fname] = models.FloatField(null=True, blank=True)
    return fields


# On utilise une classe dynamique avec les 36 champs décadaires
class SerieAnnuelle(models.Model):
    """
    Série annuelle d'un paramètre pour une station.
    Équivalent des tables pluie / fff / Tn / Tx … du mémoire.
    36 champs : d1Janv, d2Janv, d3Janv … d3Dec
    """
    station        = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='series')
    parametre      = models.CharField(max_length=10, choices=PARAMETRES, verbose_name="Paramètre")
    annee          = models.IntegerField(verbose_name="Année")
    nom            = models.CharField(max_length=100, blank=True)
    longitude      = models.FloatField(null=True, blank=True)
    latitude       = models.FloatField(null=True, blank=True)
    altitude       = models.FloatField(null=True, blank=True)

    # 36 champs décadaires
    d1Janv = models.FloatField(null=True, blank=True, verbose_name="1ère décade Janv")
    d2Janv = models.FloatField(null=True, blank=True, verbose_name="2ème décade Janv")
    d3Janv = models.FloatField(null=True, blank=True, verbose_name="3ème décade Janv")
    d1Fev  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Fév")
    d2Fev  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Fév")
    d3Fev  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Fév")
    d1Mars = models.FloatField(null=True, blank=True, verbose_name="1ère décade Mars")
    d2Mars = models.FloatField(null=True, blank=True, verbose_name="2ème décade Mars")
    d3Mars = models.FloatField(null=True, blank=True, verbose_name="3ème décade Mars")
    d1Avr  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Avr")
    d2Avr  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Avr")
    d3Avr  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Avr")
    d1Mai  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Mai")
    d2Mai  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Mai")
    d3Mai  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Mai")
    d1Juin = models.FloatField(null=True, blank=True, verbose_name="1ère décade Juin")
    d2Juin = models.FloatField(null=True, blank=True, verbose_name="2ème décade Juin")
    d3Juin = models.FloatField(null=True, blank=True, verbose_name="3ème décade Juin")
    d1Jul  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Juil")
    d2Jul  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Juil")
    d3Jul  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Juil")
    d1Aout = models.FloatField(null=True, blank=True, verbose_name="1ère décade Août")
    d2Aout = models.FloatField(null=True, blank=True, verbose_name="2ème décade Août")
    d3Aout = models.FloatField(null=True, blank=True, verbose_name="3ème décade Août")
    d1Sept = models.FloatField(null=True, blank=True, verbose_name="1ère décade Sept")
    d2Sept = models.FloatField(null=True, blank=True, verbose_name="2ème décade Sept")
    d3Sept = models.FloatField(null=True, blank=True, verbose_name="3ème décade Sept")
    d1Oct  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Oct")
    d2Oct  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Oct")
    d3Oct  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Oct")
    d1Nov  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Nov")
    d2Nov  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Nov")
    d3Nov  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Nov")
    d1Dec  = models.FloatField(null=True, blank=True, verbose_name="1ère décade Déc")
    d2Dec  = models.FloatField(null=True, blank=True, verbose_name="2ème décade Déc")
    d3Dec  = models.FloatField(null=True, blank=True, verbose_name="3ème décade Déc")

    class Meta:
        verbose_name = "Série annuelle"
        verbose_name_plural = "Séries annuelles"
        unique_together = ('station', 'parametre', 'annee')
        ordering = ['station', 'parametre', '-annee']

    def __str__(self):
        return f"{self.parametre} – {self.station.nom} – {self.annee}"

    def get_valeurs(self):
        """
        Retourne { mois_index: { '1': val, '2': val, '3': val } }
        mois_index : 1 = Janv … 12 = Déc
        """
        result = {}
        for mi, m in enumerate(MOIS_ABBR, 1):
            result[mi] = {}
            for d in range(1, 4):
                fname = f"d{d}{m}"
                result[mi][str(d)] = getattr(self, fname, None)
        return result
