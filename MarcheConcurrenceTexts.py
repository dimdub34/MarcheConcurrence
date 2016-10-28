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


def get_histo_head(role):
    header = [le2mtrans(u"Period")]
    if role == pms.ACHETEUR:
        header.append(u"Valeur")
    else:
        header.append(u"Coût")
    header.extend([u"Prix\nde\ntransaction", le2mtrans(u"Period\npayoff"),
                 le2mtrans(u"Cumulative\npayoff")])
    return header


def get_text_explanation(role, value_or_cost):
    if role == pms.ACHETEUR:
        txt = u"Vous êtes acheteur. L'unité de bien vaut pour vous {}.".format(
            get_pluriel(value_or_cost, pms.MONNAIE))
    else:
        txt = u"Vous êtes vendeur. L'unité de bien vous coûte {}.".format(
            get_pluriel(value_or_cost, pms.MONNAIE))
    return txt


def get_text_summary(period_content):
    if period_content["MC_role"] == pms.ACHETEUR:
        txt = u"Vous êtes acheteur. L'unité de bien vaut pour vous {}.".format(
            get_pluriel(period_content["MC_value_or_cost"], pms.MONNAIE))
        if period_content["MC_transaction_price"] is not None:
            txt += u" Vous avez acheté à {}.".format(
                get_pluriel(period_content["MC_transaction_price"], pms.MONNAIE))
    else:
        txt = u"Vous êtes vendeur. L'unité de bien vous coûte {}.".format(
            get_pluriel(period_content["MC_value_or_cost"], pms.MONNAIE))
        if period_content["MC_transaction_price"] is not None:
            u" Vous avez vendu à {}.".format(
                get_pluriel(period_content["MC_transaction_price"], pms.MONNAIE))
    txt += u"<br />Votre gain pour la période est de {}.".format(
        get_pluriel(period_content["MC_periodpayoff"], pms.MONNAIE))
    return txt


