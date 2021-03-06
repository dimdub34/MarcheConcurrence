# -*- coding: utf-8 -*-
"""
This module contains the texts of the part (server and remote)
"""

from util.utiltools import get_pluriel
import MarcheConcurrenceParams as pms
from util.utili18n import le2mtrans
import os
import configuration.configparam as params
import gettext
import logging

logger = logging.getLogger("le2m")
localedir = os.path.join(params.getp("PARTSDIR"), "MarcheConcurrence", "locale")
try:
    trans_MC = gettext.translation(
      "MarcheConcurrence", localedir, languages=[params.getp("LANG")]).ugettext
except IOError:
    logger.critical(u"Translation file not found")
    trans_MC = lambda x: x  # if there is an error, no translation


def get_histo_vars(role):

    histo_vars = ["MC_period", "MC_value_or_cost", "MC_transaction_price",
                  "MC_transaction_prime"]

    if (pms.TREATMENT == pms.TAXE_UNITE or pms.TREATMENT == pms.TAXE_VALEUR) and \
        role == pms.VENDEUR:
            histo_vars.append("MC_transaction_taxe")

    histo_vars.append("MC_periodpayoff")
    return histo_vars


def get_histo_head(role):
    header = [le2mtrans(u"Period")]
    if role == pms.ACHETEUR:
        header.append(u"Valeur")
    else:
        header.append(u"Coût")

    header.extend([u"Prix\nde\ntransaction", u"Prime\nde\ntransaction"])

    if (pms.TREATMENT == pms.TAXE_UNITE or pms.TREATMENT == pms.TAXE_VALEUR) and \
        role == pms.VENDEUR:
            header.append(u"Taxe")

    header.extend([le2mtrans(u"Period\npayoff")])
    return header


def get_text_explanation(role, value_or_cost):
    if role == pms.ACHETEUR:
        txt = u"Vous êtes acheteur. L'unité de bien vaut pour vous {}.".format(
            get_pluriel(value_or_cost, pms.MONNAIE))
    else:
        txt = u"Vous êtes vendeur. L'unité de bien vous coûte {}.".format(
            get_pluriel(value_or_cost, pms.MONNAIE))

        if pms.TREATMENT == pms.TAXE_UNITE:
            txt += u" Vous devez payer une taxe de {} pour la vente de votre " \
                   u"unité.".format(get_pluriel(pms.TAXE_UNITE_MONTANT, pms.MONNAIE))

        elif pms.TREATMENT == pms.TAXE_VALEUR:
            txt += u" Vous devez payer une taxe de {:.0f}% sur le prix de vente " \
                   u"de votre unité.".format(pms.TAXE_VALEUR_MONTANT * 100)
    return txt


def get_text_summary(period_content):

    if period_content["MC_role"] == pms.ACHETEUR:

        txt = u"Vous êtes acheteur. L'unité de bien vaut pour vous {}.".format(
            get_pluriel(period_content["MC_value_or_cost"], pms.MONNAIE))

        if period_content["MC_transaction_price"] is not None:
            txt += u" Vous avez acheté à {}.".format(
                get_pluriel(period_content["MC_transaction_price"], pms.MONNAIE))
        else:
            txt += u" Vous n'avez pas fait de transaction."

    else:  # vendeur

        txt = u"Vous êtes vendeur. L'unité de bien vous coûte {}.".format(
            get_pluriel(period_content["MC_value_or_cost"], pms.MONNAIE))

        if period_content["MC_transaction_price"] is not None:
            txt += u" Vous avez vendu à {}.".format(
                get_pluriel(period_content["MC_transaction_price"], pms.MONNAIE))
        else:
            txt += u" Vous n'avez pas fait de transaction."

    txt += u"<br />Votre gain pour la période est de {}.".format(
        get_pluriel(period_content["MC_periodpayoff"], pms.MONNAIE))
    return txt


def get_text_role(role):
    txt = u"Vous êtes {}".format(u"acheteur" if role == pms.ACHETEUR else u"vendeur")
    return txt


def get_text_payoff(payoff_infos):
    txt = u""
    for k, v in sorted(payoff_infos.viewitems()):
        txt += u"A la partie {} c'est la période {} qui a été tirée au sort " \
              u"pour la rémunération. Vous avez gagné {}.\n".format(
            k, v["period"], get_pluriel(v["gain_euros"], u"euro"))
    return txt
