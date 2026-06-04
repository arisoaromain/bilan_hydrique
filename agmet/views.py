import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg, Max, Min, Sum, Q

from .models import Station, Message, DonneesMeteo, DonneesAgro, SerieAnnuelle, MOIS_ABBR, PARAMETRES
from .forms import StationForm, MessageSaisieForm, RechercheForm, SerieAnnuelleRechercheForm
from .parser import parse_agmet


# ─── Accueil ─────────────────────────────────────────────────────────────────

def accueil(request):
    contexte = {
        'nb_stations':  Station.objects.count(),
        'nb_messages':  Message.objects.count(),
        'nb_valides':   Message.objects.filter(valide=True).count(),
        'nb_erreurs':   Message.objects.filter(valide=False).count(),
        'derniers_messages': Message.objects.order_by('-date_saisie')[:5],
    }
    contexte['module'] = 'agmet'
    return render(request, 'agmet/accueil.html', contexte)


# ─── Stations ─────────────────────────────────────────────────────────────────

def station_liste(request):
    stations = Station.objects.all()
    q = request.GET.get('q', '')
    if q:
        stations = stations.filter(Q(nom__icontains=q) | Q(identification__icontains=q))
    return render(request, 'agmet/station_liste.html', {'stations': stations, 'q': q})


def station_detail(request, pk):
    station = get_object_or_404(Station, pk=pk)
    messages_station = Message.objects.filter(identification=station.identification).order_by('-annee', '-mois', '-decade')
    return render(request, 'agmet/station_detail.html', {
        'station': station,
        'messages_station': messages_station,
    })


def station_creer(request):
    if request.method == 'POST':
        form = StationForm(request.POST)
        if form.is_valid():
            station = form.save()
            messages.success(request, f"Station « {station.nom} » créée avec succès.")
            return redirect('station_liste')
    else:
        form = StationForm()
    return render(request, 'agmet/station_form.html', {'form': form, 'titre': 'Nouvelle station'})


def station_modifier(request, pk):
    station = get_object_or_404(Station, pk=pk)
    if request.method == 'POST':
        form = StationForm(request.POST, instance=station)
        if form.is_valid():
            form.save()
            messages.success(request, "Station mise à jour.")
            return redirect('station_detail', pk=pk)
    else:
        form = StationForm(instance=station)
    return render(request, 'agmet/station_form.html', {'form': form, 'titre': f'Modifier – {station.nom}'})


def station_supprimer(request, pk):
    station = get_object_or_404(Station, pk=pk)
    if request.method == 'POST':
        nom = station.nom
        station.delete()
        messages.success(request, f"Station « {nom} » supprimée.")
        return redirect('station_liste')
    return render(request, 'agmet/confirmer_suppression.html', {
        'objet': station,
        'titre': f'Supprimer la station {station.nom}',
    })


# ─── Saisie et dépouillement du message AGMET ─────────────────────────────────

def message_saisir(request):
    """
    Étape 1 : l'utilisateur colle le message AGMET.
    → parsing → affichage du résultat dépouillé avec erreurs éventuelles.
    → si validé, enregistrement en base.
    """
    form = MessageSaisieForm()
    resultat = None

    if request.method == 'POST':
        if 'depouiller' in request.POST:
            form = MessageSaisieForm(request.POST)
            if form.is_valid():
                msg_brut = form.cleaned_data['message_brut']
                annee    = form.cleaned_data['annee']
                resultat = parse_agmet(msg_brut)
                resultat['message_brut'] = msg_brut
                resultat['annee'] = annee
                request.session['agmet_resultat'] = resultat
                request.session['agmet_message_brut'] = msg_brut
                request.session['agmet_annee'] = annee

        elif 'enregistrer' in request.POST:
            resultat = request.session.get('agmet_resultat')
            msg_brut = request.session.get('agmet_message_brut', '')
            annee    = request.session.get('agmet_annee')

            if resultat and annee:
                _enregistrer_message(resultat, msg_brut, annee, request)
                request.session.pop('agmet_resultat', None)
                return redirect('message_liste')

    return render(request, 'agmet/message_saisir.html', {
        'form': form,
        'resultat': resultat,
    })


def _enregistrer_message(resultat, msg_brut, annee, request):
    """Sauvegarde le message dépouillé dans toutes les tables concernées."""
    header = resultat.get('header', {})
    meteo  = resultat.get('meteo', {})
    agro   = resultat.get('agro', [])
    valide = resultat.get('valide', False)
    erreurs_txt = '\n'.join(resultat.get('erreurs', []))

    identification = header.get('identification', 'XXXXX')
    mois   = header.get('mois', '01')
    decade = header.get('decade', '51')

    # Récupérer la station
    station = Station.objects.filter(identification=identification).first()
    nom      = station.nom if station else identification
    lon      = station.longitude if station else None
    lat      = station.latitude  if station else None
    alt      = station.altitude  if station else None

    # Table Message
    msg_obj, created = Message.objects.update_or_create(
        identification=identification,
        annee=annee,
        mois=mois,
        decade=decade,
        defaults=dict(
            station=station,
            nom=nom, longitude=lon, latitude=lat, altitude=alt,
            message_brut=msg_brut,
            valide=valide,
        )
    )

    # Table DonneesMeteo
    DonneesMeteo.objects.update_or_create(
        message=msg_obj,
        defaults=dict(
            identification=identification,
            nom=nom, longitude=lon, latitude=lat, altitude=alt,
            annee=annee, mois=mois, decade=decade,
            fff=meteo.get('fff'),
            fdfdfd=meteo.get('fdfdfd'),
            tn=meteo.get('tn'),
            tx=meteo.get('tx'),
            un=meteo.get('un'),
            ux=meteo.get('ux'),
            n=meteo.get('n'),
            rrr=meteo.get('rrr'),
            id_insol=meteo.get('id_insol'),
            ev=meteo.get('ev'),
            tng=meteo.get('tng'),
            erreurs=erreurs_txt,
        )
    )

    # Table DonneesAgro
    if agro:
        cultures = agro[:3]
        defaults = dict(
            identification=identification,
            nom=nom, longitude=lon, latitude=lat, altitude=alt,
            annee=annee, mois=mois, decade=decade,
            nom_secva=resultat.get("nom_secva", ""),
        )
        for idx, c in enumerate(cultures, 1):
            defaults[f"culture{idx}"]    = c.get("culture", "")
            defaults[f"code_cult{idx}"]  = c.get("code", "")
            defaults[f"phenologie{idx}"] = c.get("phenologie", "")
            defaults[f"ennemis{idx}"]    = c.get("ennemis", "")
            defaults[f"degat{idx}"]      = c.get("degat", "")
            defaults[f"aspect{idx}"]     = c.get("aspect", "")
        DonneesAgro.objects.update_or_create(message=msg_obj, defaults=defaults)

    # Mise à jour de la SerieAnnuelle (RRR uniquement pour simplifier)
    if station and meteo.get('rrr') is not None:
        _maj_serie_annuelle(station, 'RRR', annee, mois, decade, meteo['rrr'], nom, lon, lat, alt)

    action = "créé" if created else "mis à jour"
    messages.success(request, f"Message {action} – {'✅ Valide' if valide else '⚠ Avec erreurs'}.")
    if not valide:
        messages.warning(request, f"Erreurs détectées : {erreurs_txt}")


def _maj_serie_annuelle(station, parametre, annee, mois, decade, valeur, nom, lon, lat, alt):
    """Met à jour la colonne décadaire correspondante dans SerieAnnuelle."""
    mois_map = {
        '01': 'Janv', '02': 'Fev',  '03': 'Mars', '04': 'Avr',
        '05': 'Mai',  '06': 'Juin', '07': 'Jul',  '08': 'Aout',
        '09': 'Sept', '10': 'Oct',  '11': 'Nov',  '12': 'Dec',
    }
    decade_num = {'51': '1', '52': '2', '53': '3'}.get(decade, '1')
    mois_abbr  = mois_map.get(mois, 'Janv')
    fname      = f"d{decade_num}{mois_abbr}"

    serie, _ = SerieAnnuelle.objects.get_or_create(
        station=station, parametre=parametre, annee=annee,
        defaults={'nom': nom, 'longitude': lon, 'latitude': lat, 'altitude': alt}
    )
    setattr(serie, fname, valeur)
    serie.save()


# ─── Liste des messages ───────────────────────────────────────────────────────

def message_liste(request):
    form = RechercheForm(request.GET or None)
    qs   = Message.objects.select_related('station').order_by('-annee', '-mois', '-decade')

    if form.is_valid():
        if form.cleaned_data.get('station'):
            qs = qs.filter(station=form.cleaned_data['station'])
        if form.cleaned_data.get('annee'):
            qs = qs.filter(annee=form.cleaned_data['annee'])
        if form.cleaned_data.get('mois'):
            qs = qs.filter(mois=form.cleaned_data['mois'])
        if form.cleaned_data.get('decade'):
            qs = qs.filter(decade=form.cleaned_data['decade'])

    return render(request, 'agmet/message_liste.html', {'messages_list': qs, 'form': form})


def message_detail(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    donnees_meteo = DonneesMeteo.objects.filter(message=msg).first()
    donnees_agro  = DonneesAgro.objects.filter(message=msg).first()
    return render(request, 'agmet/message_detail.html', {
        'msg': msg,
        'donnees_meteo': donnees_meteo,
        'donnees_agro':  donnees_agro,
    })


def message_supprimer(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        msg.delete()
        messages.success(request, "Message supprimé.")
        return redirect('message_liste')
    return render(request, 'agmet/confirmer_suppression.html', {
        'objet': msg,
        'titre': f'Supprimer le message {msg}',
    })


# ─── Consultation données météo ────────────────────────────────────────────────

def donnees_meteo_liste(request):
    form = RechercheForm(request.GET or None)
    qs   = DonneesMeteo.objects.order_by('-annee', '-mois', '-decade')

    if form.is_valid():
        if form.cleaned_data.get('station'):
            qs = qs.filter(identification=form.cleaned_data['station'].identification)
        if form.cleaned_data.get('annee'):
            qs = qs.filter(annee=form.cleaned_data['annee'])
        if form.cleaned_data.get('mois'):
            qs = qs.filter(mois=form.cleaned_data['mois'])
        if form.cleaned_data.get('decade'):
            qs = qs.filter(decade=form.cleaned_data['decade'])

    return render(request, 'agmet/donnees_meteo_liste.html', {'donnees': qs, 'form': form})


# ─── Consultation données agro ─────────────────────────────────────────────────

def donnees_agro_liste(request):
    form = RechercheForm(request.GET or None)
    qs   = DonneesAgro.objects.order_by('-annee', '-mois', '-decade')

    if form.is_valid():
        if form.cleaned_data.get('station'):
            qs = qs.filter(identification=form.cleaned_data['station'].identification)
        if form.cleaned_data.get('annee'):
            qs = qs.filter(annee=form.cleaned_data['annee'])
        if form.cleaned_data.get('mois'):
            qs = qs.filter(mois=form.cleaned_data['mois'])

    return render(request, 'agmet/donnees_agro_liste.html', {'donnees': qs, 'form': form})


# ─── Série annuelle (tableau décadaire) ───────────────────────────────────────

def serie_annuelle(request):
    form  = SerieAnnuelleRechercheForm(request.GET or None)
    serie = None
    tableau = None

    if form.is_valid():
        station   = form.cleaned_data['station']
        parametre = form.cleaned_data['parametre']
        annee     = form.cleaned_data['annee']
        serie = SerieAnnuelle.objects.filter(
            station=station, parametre=parametre, annee=annee
        ).first()
        if serie:
            tableau = serie.get_valeurs()

    return render(request, 'agmet/serie_annuelle.html', {
        'form': form,
        'serie': serie,
        'tableau': tableau,
        'mois_abbr': MOIS_ABBR,
        'mois_indices': list(range(1, 13)),  # 1..12 pour indexer le tableau imbriqué
    })


# ─── Export CSV ──────────────────────────────────────────────────────────────

def export_csv_meteo(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="donnees_meteo.csv"'
    response.write('\ufeff')  # BOM pour Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Station', 'Nom', 'Année', 'Mois', 'Décade',
        'fff', 'fdfdfd', 'Tmin', 'Tmax', 'Tmoy',
        'Umin', 'Umax', 'N jours pluie', 'RRR (mm)',
        'Insolation (h)', 'Évaporation (mm)', 'T sol 10cm',
    ])

    form = RechercheForm(request.GET or None)
    qs   = DonneesMeteo.objects.order_by('-annee', '-mois', '-decade')
    if form.is_valid():
        if form.cleaned_data.get('station'):
            qs = qs.filter(identification=form.cleaned_data['station'].identification)
        if form.cleaned_data.get('annee'):
            qs = qs.filter(annee=form.cleaned_data['annee'])
        if form.cleaned_data.get('mois'):
            qs = qs.filter(mois=form.cleaned_data['mois'])

    for d in qs:
        writer.writerow([
            d.identification, d.nom, d.annee, d.mois, d.decade,
            d.fff, d.fdfdfd, d.tn, d.tx, d.tm,
            d.un, d.ux, d.n, d.rrr,
            d.id_insol, d.ev, d.tng,
        ])
    return response


def export_csv_agro(request):
    """Export CSV des données agrométéorologiques (section 999 du message AGMET)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="donnees_agro.csv"'
    response.write('\ufeff')  # BOM Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Station', 'Nom', 'Année', 'Mois', 'Décade', 'SECVA',
        # Culture 1 : groupes 11CcCcF / 22ESA
        'Culture 1', 'Code C1', 'Phénologie C1 (F)', 'Ennemis C1 (E)', 'Dégâts C1 (S)', 'Aspect C1 (A)',
        # Culture 2 : groupes 33CcCcF / 44ESA
        'Culture 2', 'Code C2', 'Phénologie C2 (F)', 'Ennemis C2 (E)', 'Dégâts C2 (S)', 'Aspect C2 (A)',
        # Culture 3 : groupes 55CcCcF / 66ESA
        'Culture 3', 'Code C3', 'Phénologie C3 (F)', 'Ennemis C3 (E)', 'Dégâts C3 (S)', 'Aspect C3 (A)',
    ])

    qs = DonneesAgro.objects.order_by('-annee', '-mois', '-decade')
    for d in qs:
        writer.writerow([
            d.identification, d.nom, d.annee, d.mois, d.decade, d.nom_secva,
            d.culture1, d.code_cult1,
            d.get_phenologie1_display(), d.get_ennemis1_display(),
            d.get_degat1_display(), d.get_aspect1_display(),
            d.culture2, d.code_cult2,
            d.get_phenologie2_display(), d.get_ennemis2_display(),
            d.get_degat2_display(), d.get_aspect2_display(),
            d.culture3, d.code_cult3,
            d.get_phenologie3_display(), d.get_ennemis3_display(),
            d.get_degat3_display(), d.get_aspect3_display(),
        ])
    return response


# ─── Bilan hydrique (ETP Thornthwaite) ────────────────────────────────────────

def bilan_hydrique(request):
    """
    Calcule l'ETP selon la méthode de Thornthwaite (algorithme du mémoire, Fig. 8).
    """
    form   = RechercheForm(request.GET or None)
    result = None

    if form.is_valid():
        station = form.cleaned_data.get('station')
        annee   = form.cleaned_data.get('annee')
        if station and annee:
            donnees = DonneesMeteo.objects.filter(
                identification=station.identification,
                annee=annee,
            ).order_by('mois', 'decade')

            # Grouper par mois → température mensuelle moyenne
            from collections import defaultdict
            tm_par_mois = defaultdict(list)
            rrr_par_mois = defaultdict(float)

            for d in donnees:
                if d.tm is not None:
                    tm_par_mois[int(d.mois)].append(d.tm)
                if d.rrr is not None:
                    rrr_par_mois[int(d.mois)] += d.rrr

            result = _calcul_etp_bilan(
                tm_par_mois, rrr_par_mois,
                latitude=station.latitude, annee=annee
            )

    return render(request, 'agmet/bilan_hydrique.html', {
        'form': form,
        'result': result,
    })


def _calcul_etp_bilan(tm_par_mois, rrr_par_mois, latitude, annee):
    """
    Méthode Thornthwaite simplifiée (cf. Partie I Chapitre III du mémoire).
    Retourne une liste de dicts par mois.
    """
    # Coefficients de correction latitude (valeurs simplifiées)
    # En pratique on lirait le tableau du mémoire (Tableau 6)
    CORRECTION_LAT = {
        12: [1.04, 0.93, 1.00, 0.97, 1.02, 0.97, 1.00, 1.03, 1.00, 1.05, 0.99, 1.03],
        14: [1.05, 0.93, 1.00, 0.96, 1.01, 0.95, 0.99, 1.03, 1.00, 1.06, 0.99, 1.04],
        18: [1.07, 0.94, 1.00, 0.95, 1.00, 0.94, 0.97, 1.03, 1.00, 1.07, 0.99, 1.06],
        20: [1.08, 0.94, 1.00, 0.95, 0.99, 0.93, 0.97, 1.03, 1.00, 1.07, 0.99, 1.06],
        25: [1.10, 0.95, 1.00, 0.94, 0.98, 0.91, 0.96, 1.03, 1.00, 1.08, 0.99, 1.07],
    }
    lat_key = min(CORRECTION_LAT.keys(), key=lambda k: abs(k - abs(latitude)))
    F = CORRECTION_LAT[lat_key]

    # Indice thermique annuel I
    def indice_i(tm):
        if tm is None or tm <= 0:
            return 0
        return (tm / 5) ** 1.514

    I = sum(
        indice_i(sum(tms) / len(tms)) if tms else 0
        for tms in [tm_par_mois.get(m, []) for m in range(1, 13)]
    )

    # Exposant a
    a = 6.75e-7 * I**3 - 7.71e-5 * I**2 + 1.792e-2 * I + 0.49239

    mois_noms = ['Janv','Fév','Mars','Avr','Mai','Juin',
                 'Juil','Août','Sept','Oct','Nov','Déc']
    rows = []
    ETR_cum = 0
    RU = 100  # réserve utile du sol (mm) – valeur par défaut
    stock = RU

    for m in range(1, 13):
        tms  = tm_par_mois.get(m, [])
        tm   = sum(tms) / len(tms) if tms else None
        rrr  = rrr_par_mois.get(m, 0)

        # ETP
        if tm is None or tm <= 0:
            etp = 0.0
        elif tm >= 38:
            etp = None  # hors limites
        elif tm >= 26.5:
            etp = round((-415.85 + 32.24 * tm - 0.43 * tm**2) * F[m-1], 1)
        else:
            etp = round(16 * ((10 * tm / I) ** a) * F[m-1], 1) if I > 0 else 0.0

        # Bilan P - ETP
        diff = rrr - (etp or 0)

        # ETR et variation stock
        if diff >= 0:
            etr   = etp or 0
            stock = min(stock + diff, RU)
            deficit = 0
            excedent = max(0, stock + diff - RU)
        else:
            variation = max(diff, -stock)
            stock = max(0, stock + diff)
            etr   = rrr + abs(variation)
            deficit  = (etp or 0) - etr
            excedent = 0

        rows.append({
            'mois':     mois_noms[m - 1],
            'tm':       round(tm, 1) if tm is not None else '—',
            'rrr':      round(rrr, 1),
            'etp':      etp if etp is not None else '—',
            'diff':     round(diff, 1),
            'etr':      round(etr, 1),
            'deficit':  round(deficit, 1),
            'excedent': round(excedent, 1),
            'stock':    round(stock, 1),
        })

    return {'I': round(I, 2), 'a': round(a, 4), 'mois': rows}
