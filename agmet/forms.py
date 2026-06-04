from django import forms
from .models import Station, Message, DonneesMeteo, DonneesAgro, SerieAnnuelle, PARAMETRES, MOIS_ABBR


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['identification', 'nom', 'type_station', 'longitude', 'latitude', 'altitude']
        widgets = {
            'identification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 32155'}),
            'nom':            forms.TextInput(attrs={'class': 'form-control'}),
            'type_station':   forms.Select(attrs={'class': 'form-select'}),
            'longitude':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'latitude':       forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'altitude':       forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        }


class MessageSaisieForm(forms.Form):
    """Formulaire principal : saisie du message AGMET brut."""
    message_brut = forms.CharField(
        label="Message AGMET",
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 6,
            'placeholder': (
                "AGMET 51011 32155 03145 13087 40285 60305 "
                "85575 7777 10205 21254 01023 10125 20124\n"
                "444 0102 51211 0100 0100 0101"
            ),
        }),
        help_text="Collez ici le message AGMET complet tel que reçu."
    )
    annee = forms.IntegerField(
        label="Année",
        min_value=1950, max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    def clean_message_brut(self):
        msg = self.cleaned_data['message_brut'].strip()
        if not msg.upper().startswith('AGMET'):
            raise forms.ValidationError("Le message doit commencer par 'AGMET'.")
        return msg


class RechercheForm(forms.Form):
    """Formulaire de recherche / consultation des données."""
    MOIS_CHOICES = [('', '-- Tous --')] + [
        (f'{i:02d}', m) for i, m in enumerate(
            ['Janvier','Février','Mars','Avril','Mai','Juin',
             'Juillet','Août','Septembre','Octobre','Novembre','Décembre'], 1
        )
    ]
    DECADE_CHOICES = [
        ('', '-- Toutes --'),
        ('51', '1ère décade'),
        ('52', '2ème décade'),
        ('53', '3ème décade'),
    ]

    station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        required=False,
        empty_label="-- Toutes les stations --",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    annee = forms.IntegerField(
        required=False,
        min_value=1950, max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2021'}),
    )
    mois = forms.ChoiceField(
        choices=MOIS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    decade = forms.ChoiceField(
        choices=DECADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class SerieAnnuelleRechercheForm(forms.Form):
    """Recherche d'une série annuelle (tableau décadaire)."""
    station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        empty_label="-- Choisir une station --",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    parametre = forms.ChoiceField(
        choices=PARAMETRES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    annee = forms.IntegerField(
        min_value=1950, max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2021'}),
    )
