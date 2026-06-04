"""
Calculs du Bilan Hydrique
Méthodes : Thornthwaite et Turc
Variables : ETP, ETR, RFU, DA, Variation de Stockage
"""

import math


# ─────────────────────────────────────────────────────────
# COEFFICIENTS DE CORRECTION PHOTOTHERMIQUE (Thornthwaite)
# Nombre de jours et heures de lumière par mois selon latitude
# ─────────────────────────────────────────────────────────

# Correction K = (Nj/30) * (Nhs/12)  où Nj=nb jours mois, Nhs=durée journée solaire moy
# Valeurs de correction K pour l'hémisphère SUD (latitude négative)
# Index 0=Jan, 11=Déc
CORRECTION_K_SUD = {
    # lat  : [Jan, Fév, Mar, Avr, Mai, Jun, Jul, Aoû, Sep, Oct, Nov, Déc]
    -5:  [1.04, 0.94, 1.04, 1.01, 1.04, 1.01, 1.04, 1.04, 1.01, 1.04, 1.01, 1.04],
    -10: [1.06, 0.95, 1.04, 1.00, 1.02, 0.99, 1.02, 1.03, 1.01, 1.05, 1.02, 1.06],
    -15: [1.08, 0.96, 1.04, 0.99, 1.01, 0.97, 1.00, 1.02, 1.01, 1.06, 1.03, 1.08],
    -20: [1.10, 0.97, 1.05, 0.99, 0.99, 0.96, 0.99, 1.01, 1.01, 1.06, 1.05, 1.11],
    -25: [1.13, 0.98, 1.05, 0.98, 0.97, 0.94, 0.97, 1.00, 1.01, 1.08, 1.06, 1.13],
    -30: [1.16, 0.99, 1.05, 0.97, 0.95, 0.92, 0.95, 0.99, 1.01, 1.09, 1.08, 1.16],
    -35: [1.19, 1.00, 1.06, 0.96, 0.93, 0.89, 0.92, 0.98, 1.01, 1.10, 1.10, 1.19],
    -40: [1.22, 1.01, 1.06, 0.95, 0.90, 0.87, 0.90, 0.97, 1.01, 1.12, 1.12, 1.23],
    -45: [1.25, 1.02, 1.06, 0.94, 0.88, 0.84, 0.87, 0.96, 1.01, 1.13, 1.14, 1.26],
    -50: [1.29, 1.03, 1.06, 0.93, 0.85, 0.81, 0.84, 0.95, 1.01, 1.15, 1.17, 1.30],
}

MOIS_JOURS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def get_correction_k(latitude: float, mois: int) -> float:
    """Interpolation du facteur K de Thornthwaite selon latitude."""
    lats = sorted(CORRECTION_K_SUD.keys())
    if latitude <= lats[-1]:
        return CORRECTION_K_SUD[lats[-1]][mois - 1]
    if latitude >= lats[0]:
        return CORRECTION_K_SUD[lats[0]][mois - 1]
    # Interpolation linéaire
    for i in range(len(lats) - 1):
        if lats[i] >= latitude >= lats[i + 1]:
            l1, l2 = lats[i], lats[i + 1]
            k1 = CORRECTION_K_SUD[l1][mois - 1]
            k2 = CORRECTION_K_SUD[l2][mois - 1]
            t = (latitude - l1) / (l2 - l1)
            return k1 + t * (k2 - k1)
    return 1.0


# ─────────────────────────────────────────────────────────
# MÉTHODE THORNTHWAITE
# ─────────────────────────────────────────────────────────

def etp_thornthwaite(temperatures_mensuelles: list, latitude: float, annee: int = None) -> list:
    """
    Calcule l'ETP mensuelle par la méthode de Thornthwaite.

    Parameters
    ----------
    temperatures_mensuelles : list de 12 valeurs (T° moy mensuelle °C)
    latitude : latitude en degrés décimaux (négatif = hémisphère sud)
    annee : année (pour détecter les années bissextiles)

    Returns
    -------
    list de 12 valeurs ETP (mm/mois)
    """
    T = temperatures_mensuelles

    # Indice thermique annuel I
    I = sum(max((t / 5) ** 1.514, 0) for t in T)

    # Exposant alpha
    alpha = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.792e-2 * I) + 0.49239

    etp_list = []
    for m in range(12):
        mois = m + 1
        Tm = max(T[m], 0)

        if Tm == 0:
            etp_non_corr = 0.0
        elif Tm > 26.5:
            # Formule directe pour T > 26.5°C
            etp_non_corr = -415.85 + 32.24 * Tm - 0.43 * Tm**2
        else:
            etp_non_corr = 16.0 * (10 * Tm / I) ** alpha

        # Correction photothermique K
        K = get_correction_k(latitude, mois)
        etp = etp_non_corr * K

        # Correction pour année bissextile
        if annee and mois == 2 and _is_leap(annee):
            etp = etp * 29 / 28

        etp_list.append(round(max(etp, 0), 2))

    return etp_list


def _is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


# ─────────────────────────────────────────────────────────
# MÉTHODE TURC
# ─────────────────────────────────────────────────────────

def etp_turc(temperatures_mensuelles: list, insolations_mensuelles: list,
             humidites_mensuelles: list = None) -> list:
    """
    Calcule l'ETP mensuelle par la méthode de Turc.

    ETP = 0.40 * (T/(T+15)) * (Rg + 50)       si H >= 50%
    ETP = 0.40 * (T/(T+15)) * (Rg + 50) * (1 + (50-H)/70)  si H < 50%

    Parameters
    ----------
    temperatures_mensuelles : list 12 valeurs T° (°C)
    insolations_mensuelles  : list 12 valeurs insolation (Wh/m²/mois → convertie en cal/cm²/j)
    humidites_mensuelles    : list 12 valeurs humidité (%) — optionnel

    Returns
    -------
    list 12 valeurs ETP (mm/mois)
    """
    etp_list = []
    for m in range(12):
        T = temperatures_mensuelles[m]
        # Conversion Wh/m² → cal/cm²/jour
        # 1 Wh/m² = 0.0860 Mcal/m² ; 1 cal/cm² = 1 langley
        # Rg mensuel (Wh/m²) → Rg journalier (cal/cm²/j)
        nj = MOIS_JOURS[m]
        Rg_wh_mois = insolations_mensuelles[m]
        Rg = (Rg_wh_mois / nj) * 0.0860  # cal/cm²/jour (1 Wh/m² = 0.0860 cal/cm²)

        if T <= 0:
            etp_list.append(0.0)
            continue

        etp_base = 0.40 * (T / (T + 15)) * (Rg + 50) * nj / 30

        # Correction humidité
        if humidites_mensuelles:
            H = humidites_mensuelles[m]
            if H < 50:
                etp_base = etp_base * (1 + (50 - H) / 70)

        etp_list.append(round(max(etp_base, 0), 2))

    return etp_list


# ─────────────────────────────────────────────────────────
# BILAN HYDRIQUE : ETR, RFU, DA, ΔS
# ─────────────────────────────────────────────────────────

def calcul_bilan(precipitations: list, etp_list: list,
                 rfu_max: float = 100.0) -> dict:
    """
    Calcul complet du bilan hydrique mensuel.

    Paramètres
    ----------
    precipitations : list de 12 valeurs P (mm/mois)
    etp_list       : list de 12 valeurs ETP (mm/mois)
    rfu_max        : Réserve en eau maximale du sol (mm) — défaut 100 mm

    Retourne
    --------
    dict avec listes mensuelles :
        etr, rfu, da, variation_stock, excedent
    """
    etr = []
    rfu = []
    da = []
    variation_stock = []
    excedent = []

    rfu_prec = rfu_max / 2  # stock initial = demi-capacité

    for m in range(12):
        P = precipitations[m]
        ETP = etp_list[m]
        bilan = P - ETP

        if bilan >= 0:
            # Excédent hydrique
            ETR_m = ETP
            nouveau_stock = min(rfu_prec + bilan, rfu_max)
            exc = (rfu_prec + bilan) - nouveau_stock  # ruissellement
        else:
            # Déficit : on puise dans le stock
            besoin = abs(bilan)
            puise = min(besoin, rfu_prec)
            ETR_m = P + puise
            nouveau_stock = rfu_prec - puise
            exc = 0.0

        DA_m = max(ETP - ETR_m, 0)
        dS = nouveau_stock - rfu_prec

        etr.append(round(ETR_m, 2))
        rfu.append(round(nouveau_stock, 2))
        da.append(round(DA_m, 2))
        variation_stock.append(round(dS, 2))
        excedent.append(round(exc, 2))

        rfu_prec = nouveau_stock

    return {
        'etr': etr,
        'rfu': rfu,
        'da': da,
        'variation_stock': variation_stock,
        'excedent': excedent,
    }


# ─────────────────────────────────────────────────────────
# CALCUL ANNUEL COMPLET
# ─────────────────────────────────────────────────────────

def calcul_annuel_complet(donnees_annuelles: dict, latitude: float,
                          methode: str = 'thornthwaite',
                          rfu_max: float = 100.0) -> dict:
    """
    Lance le calcul complet pour une année donnée.

    donnees_annuelles : {
        'temperatures': [T_jan, ..., T_dec],
        'precipitations': [P_jan, ..., P_dec],
        'insolations': [I_jan, ..., I_dec],   # pour Turc
        'humidites': [H_jan, ..., H_dec],      # pour Turc
        'annee': int
    }
    """
    T = donnees_annuelles['temperatures']
    P = donnees_annuelles['precipitations']
    I = donnees_annuelles.get('insolations', [0]*12)
    H = donnees_annuelles.get('humidites', [None]*12)
    annee = donnees_annuelles.get('annee')

    if methode == 'thornthwaite':
        etp_list = etp_thornthwaite(T, latitude, annee)
    else:  # turc
        H_val = H if any(h is not None for h in H) else None
        etp_list = etp_turc(T, I, H_val)

    bilan = calcul_bilan(P, etp_list, rfu_max)
    bilan['etp'] = etp_list

    return bilan
