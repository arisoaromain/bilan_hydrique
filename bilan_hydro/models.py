from django.db import models


class Station(models.Model):
    nom = models.CharField(max_length=100)
    latitude = models.FloatField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Station météo"


class DonneesMensuelles(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='donnees')
    annee = models.IntegerField()
    mois = models.IntegerField()  # 1-12
    temperature_moy = models.FloatField(help_text="Température moyenne mensuelle (°C)")
    precipitation = models.FloatField(help_text="Précipitations totales mensuelles (mm)")
    humidite_moy = models.FloatField(null=True, blank=True, help_text="Humidité relative moyenne (%)")
    insolation = models.FloatField(null=True, blank=True, help_text="Insolation totale (Wh/m²)")

    class Meta:
        unique_together = ('station', 'annee', 'mois')
        ordering = ['annee', 'mois']

    def __str__(self):
        return f"{self.station.nom} - {self.annee}/{self.mois:02d}"


class BilanHydro(models.Model):
    METHODE_CHOICES = [
        ('thornthwaite', 'Thornthwaite'),
        ('turc', 'Turc'),
    ]
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='bilans')
    methode = models.CharField(max_length=20, choices=METHODE_CHOICES)
    annee = models.IntegerField()
    mois = models.IntegerField()

    # Résultats calculés
    etp = models.FloatField(help_text="Évapotranspiration potentielle (mm)")
    etr = models.FloatField(help_text="Évapotranspiration réelle (mm)")
    rfu = models.FloatField(help_text="Réserve Facilement Utilisable (mm)")
    da = models.FloatField(help_text="Déficit Agricole (mm)")
    variation_stock = models.FloatField(help_text="Variation de stockage (mm)")
    excedent = models.FloatField(default=0, help_text="Excédent / Ruissellement (mm)")

    class Meta:
        unique_together = ('station', 'methode', 'annee', 'mois')
        ordering = ['annee', 'mois']

    def __str__(self):
        return f"{self.station.nom} [{self.methode}] {self.annee}/{self.mois:02d}"
