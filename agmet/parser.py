"""
agmet/parser.py
───────────────
Dépouillement du message AGMET selon la FORME SYMBOLIQUE du mémoire
(Section II.2.1 – Formes Complètes, station synoptique) :

  1ère section : AGMET  Y1Y1MMA  IIiii  (ou Nom en clair)
  2ème section : 666  (Omfff)  (1mfdfdfd)  4SnTnTnTn  6SnTxTxTx  (8UnUnUxUx)
  3ème section : 777  1qann  (2RRRr)
  4ème section : 888  OldIdIdId  1MEvEvEv  2SnTngTngTng
  5ème section : Nom_SECVA  999
                 11C1C1F1  22E1S1A1
                 33C2C2F2  44E2S2A2
                 55C3C3F3  66E3S3A3
                 FIN MESSAGE
"""

import re

# ─── Limites de contrôle ─────────────────────────────────────────────────────
LIMITES = {
    'fff':    (0,    9999),
    'fdfdfd': (0,    9999),
    'tn':     (-30,  45),
    'tx':     (-30,  50),
    'un':     (0,    100),
    'ux':     (0,    100),
    'n':      (0,    10),
    'rrr':    (0,    9999),
    'id':     (0,    240),
    'ev':     (0,    300),
    'tng':    (-20,  40),
}

MOIS_NOM = {
    '01':'Janvier','02':'Février','03':'Mars','04':'Avril',
    '05':'Mai','06':'Juin','07':'Juillet','08':'Août',
    '09':'Septembre','10':'Octobre','11':'Novembre','12':'Décembre',
}

DECADE_NOM = {
    '51':'1ère décade (1–10)',
    '52':'2ème décade (11–20)',
    '53':'3ème décade (21–fin)',
}

# Codes culture (CcCc) — 2 chiffres
CULTURE_CODES = {
    '01':'Riz',       '02':'Maïs',      '03':'Manioc',
    '04':'Patate douce','05':'Haricot', '06':'Arachide',
    '07':'Canne à sucre','08':'Coton',  '09':'Vanille',
    '10':'Café',      '11':'Girofle',   '12':'Poivre',
    '13':'Blé',       '14':'Sorgho',    '15':'Tabac',
    '99':'Autre',
}

# Codes phénologie (F)
PHENOLOGIE = {
    '0':'Pas observable','1':'Semis/plantation','2':'Levée/germination',
    '3':'Tallage/végétatif','4':'Montaison/épiaison','5':'Floraison',
    '6':'Fructification','7':'Maturation','8':'Récolte','9':'Jachère',
}

# Codes ennemis (E)
ENNEMIS = {
    '0':'Aucun','1':'Insectes','2':'Maladies fongiques','3':'Maladies virales',
    '4':'Mauvaises herbes','5':'Oiseaux','6':'Rongeurs','7':'Sécheresse',
    '8':'Excès d\'eau','9':'Autre',
}

# Codes dégâts (S) et aspect général (A)
DEGATS  = {'0':'Aucun','1':'Léger','2':'Modéré','3':'Grave','4':'Perte totale'}
ASPECTS = {'1':'Très bon','2':'Bon','3':'Moyen','4':'Mauvais','5':'Très mauvais'}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _int(s):
    try: return int(s)
    except: return None

def _float(s):
    try: return float(s)
    except: return None

def _controle(nom, val, erreurs):
    if val is None or nom not in LIMITES:
        return
    lo, hi = LIMITES[nom]
    if not (lo <= val <= hi):
        erreurs.append(f"⚠ {nom.upper()} = {val} hors limites [{lo}, {hi}]")

def _decode_temp(sn, val_str):
    """Sn=0/2 → positif, Sn=1/3 → négatif. Valeur en dixièmes de °C."""
    if sn is None or val_str is None or '/' in str(sn)+str(val_str):
        return None
    signe = -1 if str(sn) in ('1','3') else 1
    v = _float(val_str)
    return round(signe * v / 10, 1) if v is not None else None

def _slash(s):
    """True si le groupe contient des barres obliques (donnée manquante)."""
    return '/' in s


# ─── Parseur principal ────────────────────────────────────────────────────────

def parse_agmet(message_brut: str) -> dict:
    """
    Analyse un message AGMET complet et retourne :
    {
      'header'  : {decade, mois, type_station, identification},
      'meteo'   : {fff, fdfdfd, tn, tx, tm, un, ux, n, rrr, id_insol, ev, tng},
      'agro'    : [ {culture, phenologie, ennemis, degat, aspect}, ... ],
      'nom_secva': str,
      'erreurs' : [...],
      'valide'  : bool,
    }
    """
    erreurs = []
    tokens  = message_brut.upper().split()
    result  = {
        'header':    {},
        'meteo':     {},
        'agro':      [],
        'nom_secva': '',
        'erreurs':   erreurs,
        'valide':    False,
    }

    if not tokens:
        erreurs.append("❌ Message vide.")
        return result

    # ══════════════════════════════════════════════════════════════════════════
    # 1ÈRE SECTION : AGMET  Y1Y1MMA  IIiii
    # ══════════════════════════════════════════════════════════════════════════
    if tokens[0] != 'AGMET':
        erreurs.append("❌ Le message doit commencer par 'AGMET'.")
        return result

    if len(tokens) < 3:
        erreurs.append("❌ Message incomplet (manque groupe dateur ou identification).")
        return result

    # Groupe dateur Y1Y1MMA  (ex: 51011  ou  52031)
    dateur = tokens[1]
    m_dat  = re.match(r'^(51|52|53)(0[1-9]|1[0-2])([1-69])$', dateur)
    if not m_dat:
        erreurs.append(f"⚠ Groupe dateur '{dateur}' invalide (attendu : 51|52|53 + MM + A).")
    else:
        result['header'] = {
            'decade'        : m_dat.group(1),
            'decade_label'  : DECADE_NOM.get(m_dat.group(1), m_dat.group(1)),
            'mois'          : m_dat.group(2),
            'mois_label'    : MOIS_NOM.get(m_dat.group(2), m_dat.group(2)),
            'type_station'  : m_dat.group(3),
        }

    # Identification IIiii (5 chiffres) ou nom en clair
    result['header']['identification'] = tokens[2]

    # Index courant
    i = 3

    # ══════════════════════════════════════════════════════════════════════════
    # 2ÈME SECTION : 666  (Omfff)  (1mfdfdfd)  4SnTnTnTn  6SnTxTxTx  (8UnUnUxUx)
    # ══════════════════════════════════════════════════════════════════════════
    if i < len(tokens) and tokens[i] == '666':
        i += 1  # consommer le marqueur 666

    while i < len(tokens):
        tok = tokens[i]

        if tok in ('777', '888', '999') or tok == 'FIN':
            break

        # Omfff : commence par 0, longueur 5 ex: 03145
        if re.match(r'^0[2-9]\d{3}$', tok):
            fff = _float(tok[2:])
            _controle('fff', fff, erreurs)
            result['meteo']['fff']   = fff
            result['meteo']['fff_m'] = tok[1]  # type de mesure

        # 1mfdfdfd : commence par 1, longueur 6 ex: 13087
        elif re.match(r'^1[2-9]\d{4}$', tok):
            fdfdfd = _float(tok[2:])
            _controle('fdfdfd', fdfdfd, erreurs)
            result['meteo']['fdfdfd']   = fdfdfd
            result['meteo']['fdfdfd_m'] = tok[1]

        # 4SnTnTnTn : température minimale
        elif re.match(r'^4[0-3]\d{3}$', tok) and not _slash(tok):
            tn = _decode_temp(tok[1], tok[2:])
            _controle('tn', tn, erreurs)
            result['meteo']['tn'] = tn

        # 6SnTxTxTx : température maximale
        elif re.match(r'^6[0-3]\d{3}$', tok) and not _slash(tok):
            tx = _decode_temp(tok[1], tok[2:])
            _controle('tx', tx, erreurs)
            result['meteo']['tx'] = tx
            # Contrôle croisé Tn vs Tx
            tn = result['meteo'].get('tn')
            if tn is not None and tx is not None and tn > tx:
                erreurs.append(f"⚠ Incohérence : Tmin ({tn}°C) > Tmax ({tx}°C)")

        # 8UnUnUxUx : humidité min/max
        elif re.match(r'^8\d{4}$', tok) and not _slash(tok):
            un = _int(tok[1:3])
            ux = _int(tok[3:5])
            un = 100 if un == 0 else un   # 00 = 100%
            ux = 100 if ux == 0 else ux
            _controle('un', un, erreurs)
            _controle('ux', ux, erreurs)
            if un is not None and ux is not None and un > ux:
                erreurs.append(f"⚠ Humidité min ({un}%) > max ({ux}%)")
            result['meteo']['un'] = un
            result['meteo']['ux'] = ux

        i += 1

    # Calcul Tmoy
    tn = result['meteo'].get('tn')
    tx = result['meteo'].get('tx')
    if tn is not None and tx is not None:
        result['meteo']['tm'] = round((tn + tx) / 2, 1)

    # ══════════════════════════════════════════════════════════════════════════
    # 3ÈME SECTION : 777  1qann  (2RRRr)
    # ══════════════════════════════════════════════════════════════════════════
    if i < len(tokens) and tokens[i] == '777':
        i += 1

        while i < len(tokens):
            tok = tokens[i]
            if tok in ('888', '999') or tok == 'FIN':
                break

            # 1qann : qualité + occurrence + nb jours pluie
            if re.match(r'^1[0-28]\d{3}$', tok):
                q  = tok[1]   # qualité (0=complet, 1=1 obs manquante, 2=2 manquantes, 8=>2)
                a  = tok[2]   # occurrence (0=pas de pluie, 1=traces, 2=mesurable, 3=≥10000mm)
                nn = _int(tok[3:5])
                _controle('n', nn, erreurs)
                result['meteo']['qualite_pluie']    = q
                result['meteo']['occurrence_pluie'] = a
                result['meteo']['n']                = nn

            # 2RRRr : précipitation (en dixièmes de mm → divisé par 10)
            elif re.match(r'^2\d{4}$', tok) and not _slash(tok):
                rrr = _float(tok[1:]) / 10
                _controle('rrr', rrr, erreurs)
                result['meteo']['rrr'] = rrr

            i += 1

    # ══════════════════════════════════════════════════════════════════════════
    # 4ÈME SECTION : 888  OldIdIdId  1MEvEvEv  2SnTngTngTng
    # ══════════════════════════════════════════════════════════════════════════
    if i < len(tokens) and tokens[i] == '888':
        i += 1

        while i < len(tokens):
            tok = tokens[i]
            if tok == '999' or tok == 'FIN':
                break

            # OldIdIdId : insolation (O=0, l=indicateur, dIdIdId en dixièmes d'heure)
            # Format : commence par 0, longueur 5, ex: 01023
            if re.match(r'^0\d{4}$', tok) and not _slash(tok):
                id_val = _float(tok[1:]) / 10
                _controle('id', id_val, erreurs)
                result['meteo']['id_insol'] = id_val

            # 1MEvEvEv : évaporation totale (en mm entier)
            # Format : commence par 1, indicateur M (0 ou 5), longueur 5 ex: 10125
            elif re.match(r'^1[05]\d{3}$', tok) and not _slash(tok):
                ev = _float(tok[2:])
                _controle('ev', ev, erreurs)
                result['meteo']['ev'] = ev

            # 2SnTngTngTng : température sol à 10 cm
            elif re.match(r'^2[0-3]\d{3}$', tok) and not _slash(tok):
                tng = _decode_temp(tok[1], tok[2:])
                _controle('tng', tng, erreurs)
                result['meteo']['tng'] = tng

            i += 1

    # ══════════════════════════════════════════════════════════════════════════
    # 5ÈME SECTION : Nom_SECVA  999
    #                11C1C1F1  22E1S1A1
    #                33C2C2F2  44E2S2A2
    #                55C3C3F3  66E3S3A3
    #                FIN MESSAGE
    # ══════════════════════════════════════════════════════════════════════════
    if i < len(tokens):
        # Le nom de la SECVA précède le marqueur 999
        nom_parts = []
        while i < len(tokens) and tokens[i] != '999' and tokens[i] != 'FIN':
            nom_parts.append(tokens[i])
            i += 1
        result['nom_secva'] = ' '.join(nom_parts)

    if i < len(tokens) and tokens[i] == '999':
        i += 1  # consommer 999

    # Cultures : groupes par paires  11CcCcF  22EsSsAs  (culture 1)
    #                                33CcCcF  44EsSsAs  (culture 2)
    #                                55CcCcF  66EsSsAs  (culture 3)
    cultures_raw = {}  # {numero_culture: {'C':..,'F':..,'E':..,'S':..,'A':..}}

    while i < len(tokens):
        tok = tokens[i]

        if tok in ('FIN', 'MESSAGE'):
            i += 1
            continue

        # 11CcCcF : culture 1 (préfixe 11)
        m = re.match(r'^(11|33|55)(\d{2})(\d)$', tok)
        if m:
            prefix = m.group(1)
            num    = {'11': 1, '33': 2, '55': 3}[prefix]
            cc     = m.group(2)
            f      = m.group(3)
            cultures_raw.setdefault(num, {})
            cultures_raw[num]['code'] = cc
            cultures_raw[num]['culture'] = CULTURE_CODES.get(cc, f"Culture {cc}")
            cultures_raw[num]['phenologie'] = f
            cultures_raw[num]['phenologie_label'] = PHENOLOGIE.get(f, f)
            i += 1
            continue

        # 22EsSsAs : ennemis/dégâts/aspect culture 1 (préfixe 22)
        m2 = re.match(r'^(22|44|66)(\d)(\d)(\d)$', tok)
        if m2:
            prefix = m2.group(1)
            num    = {'22': 1, '44': 2, '66': 3}[prefix]
            e      = m2.group(2)
            s      = m2.group(3)
            a      = m2.group(4)
            cultures_raw.setdefault(num, {})
            cultures_raw[num]['ennemis']       = e
            cultures_raw[num]['ennemis_label'] = ENNEMIS.get(e, e)
            cultures_raw[num]['degat']         = s
            cultures_raw[num]['degat_label']   = DEGATS.get(s, s)
            cultures_raw[num]['aspect']        = a
            cultures_raw[num]['aspect_label']  = ASPECTS.get(a, a)
            i += 1
            continue

        i += 1

    # Trier et ajouter les cultures au résultat
    for num in sorted(cultures_raw.keys()):
        result['agro'].append(cultures_raw[num])

    # ── Validation finale ─────────────────────────────────────────────────────
    result['valide'] = len(erreurs) == 0

    return result
