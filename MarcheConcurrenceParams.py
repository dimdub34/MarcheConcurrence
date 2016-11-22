# -*- coding: utf-8 -*-

"""=============================================================================
This modules contains the variables and the parameters.
Do not change the variables.
Parameters that can be changed without any risk of damages should be changed
by clicking on the configure sub-menu at the server screen.
If you need to change some parameters below please be sure of what you do,
which means that you should ask to the developer ;-)
============================================================================="""

from datetime import time
import random

# variables --------------------------------------------------------------------
BASELINE = 0
TAXE_UNITE = 1
TAXE_VALEUR = 2
TREATMENTS_NAMES = {BASELINE: u"Baseline", TAXE_UNITE: u"Taxe unité",
                    TAXE_VALEUR: u"Taxe valeur"}
ACHETEUR = 0
VENDEUR = 1
OFFRE_ACHAT = 0
OFFRE_VENTE = 1

# parameters -------------------------------------------------------------------
COUTS = [5, 5, 10, 15, 20, 25, 30, 35, 40, 45]
VALEURS = [55, 55, 50, 45, 40, 35, 30, 25, 20, 15]
TEMPS = time(0, 2, 0)  # heures, minutes, secondes
TREATMENT = BASELINE
TAUX_CONVERSION = 1
NOMBRE_PERIODES = 10
TAILLE_GROUPES = 20
GROUPES_CHAQUE_PERIODE = False
MONNAIE = u"euro"
DECIMALES = 1
FORFAIT_TRANSACTION = 0.1
PERIODE_ESSAI = True
TAXE_UNITE_MONTANT = 20
TAXE_VALEUR_MONTANT = 0.50

# DECISION
DECISION_MIN = 0
DECISION_MAX = 500
