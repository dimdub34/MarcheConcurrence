# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
from twisted.internet import defer
from random import choice, randint
from util import utiltools
from util.utili18n import le2mtrans
import MarcheConcurrenceParams as pms
from MarcheConcurrenceGui import DConfigure

logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur(object):
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv
        self._current_sequence = 0

        # creation of the menu (will be placed in the "part" menu on the
        # server screen)
        actions = OrderedDict()
        actions[le2mtrans(u"Configure")] = self._configure
        actions[le2mtrans(u"Display parameters")] = \
            lambda _: self._le2mserv.gestionnaire_graphique. \
            display_information2(
                utiltools.get_module_info(pms), le2mtrans(u"Parameters"))
        actions[le2mtrans(u"Start")] = lambda _: self._demarrer()
        actions[u"Afficher les gains sur les postes"] = lambda _: self._display_payoffs()
        self._le2mserv.gestionnaire_graphique.add_topartmenu(
            u"Marché - Concurrence", actions)

    def _configure(self):
        screen_conf = DConfigure(self._le2mserv.gestionnaire_graphique.screen)
        if screen_conf.exec_():
            self._le2mserv.gestionnaire_graphique.infoserv(u"Traitement: {}".format(
                pms.TREATMENTS_NAMES.get(pms.TREATMENT)))
            self._le2mserv.gestionnaire_graphique.infoserv(u"Période d'essai: {}".format(
                u"oui" if pms.PERIODE_ESSAI else u"non"))
            self._le2mserv.gestionnaire_graphique.infoserv(u"Durée du marché: {}".format(
                pms.TEMPS))

    @defer.inlineCallbacks
    def _demarrer(self):
        """
        Start the part
        :return:
        """
        # check conditions -----------------------------------------------------
        if not self._le2mserv.gestionnaire_graphique.question(
                        le2mtrans(u"Start") + u" MarcheConcurrence?"):
            return

        # init part ============================================================
        yield (self._le2mserv.gestionnaire_experience.init_part(
            "MarcheConcurrence", "PartieMC", "RemoteMC", pms))
        self._tous = self._le2mserv.gestionnaire_joueurs.get_players(
            'MarcheConcurrence')

        # increment sequence
        self._current_sequence += 1
        self._le2mserv.gestionnaire_graphique.infoserv(u"Sequence {}".format(
            self._current_sequence))

        if self._current_sequence == 1:

            # form groups ------------------------------------------------------
            try:
                self._le2mserv.gestionnaire_groupes.former_groupes(
                    self._le2mserv.gestionnaire_joueurs.get_players(),
                    pms.TAILLE_GROUPES, forcer_nouveaux=True)
            except ValueError as e:
                self._le2mserv.gestionnaire_graphique.display_error(
                    e.message)
                return

            # set roles --------------------------------------------------------
            self._le2mserv.gestionnaire_graphique.infoserv(u"*** Roles ***")
            for num, comp in self._le2mserv.gestionnaire_groupes.get_groupes().viewitems():
                for i, m in enumerate(comp):
                    if i % 2:
                        setattr(m, "role", pms.ACHETEUR)
                    else:
                        setattr(m, "role", pms.VENDEUR)
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{} - Buyers: {}".format(
                        num.split("_")[2],
                        [j for j in comp if j.role == pms.ACHETEUR]))
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{} - Sellers: {}".format(
                        num.split("_")[2],
                        [j for j in comp if j.role == pms.VENDEUR]))

            # display roles
            yield (self._le2mserv.gestionnaire_experience.run_step(
                u"Display roles", self._tous, "display_role"))

        # configure remotes ----------------------------------------------------
        yield (self._le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Configure"), self._tous, "configure", self._current_sequence))

        # Start repetitions ====================================================

        period_start = 0 if pms.NOMBRE_PERIODES == 0 or pms.PERIODE_ESSAI else 1
        for period in range(period_start, pms.NOMBRE_PERIODES + 1):

            if self._le2mserv.gestionnaire_experience.stop_repetitions:
                break

            # init period ------------------------------------------------------
            self._le2mserv.gestionnaire_graphique.infoserv(
                [None, le2mtrans(u"Period") + u" {}".format(period)])
            self._le2mserv.gestionnaire_graphique.infoclt(
                [None, le2mtrans(u"Period") + u" {}".format(period)],
                fg="white", bg="gray")
            yield (self._le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", period))

            # attribution des couts / valeurs ----------------------------------
            for num, comp in self._le2mserv.gestionnaire_groupes.get_groupes(
                    "MarcheConcurrence").viewitems():
                # buyers
                values = pms.VALEURS[:pms.TAILLE_GROUPES/2]
                buyers = [j for j in comp if j.joueur.role == pms.ACHETEUR]
                buyers_values = []
                for j in buyers:
                    val = choice(values)
                    j.currentperiod.MC_value_or_cost = val
                    values.remove(val)
                    buyers_values.append((j.joueur, val))
                # sellers
                costs = pms.COUTS[:pms.TAILLE_GROUPES/2]
                sellers = [j for j in comp if j.joueur.role == pms.VENDEUR]
                sellers_costs = []
                for j in sellers:
                    cost = choice(costs)
                    j.currentperiod.MC_value_or_cost = cost
                    costs.remove(cost)
                    sellers_costs.append((j.joueur, cost))
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{} - Buyers' values: {}".format(num.split("_")[2],
                                                       buyers_values))
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{} - Sellers' costs: {}".format(num.split("_")[2],
                                                       sellers_costs))

            # decision
            yield(self._le2mserv.gestionnaire_experience.run_step(
                le2mtrans(u"Decision"), self._tous, "display_decision"))
            
            # period payoffs
            self._le2mserv.gestionnaire_experience.compute_periodpayoffs(
                "MarcheConcurrence")
        
            # summary
            yield(self._le2mserv.gestionnaire_experience.run_step(
                le2mtrans(u"Summary"), self._tous, "display_summary"))
        
        # End of part ==========================================================
        selected_period = randint(1, pms.NOMBRE_PERIODES)
        self._le2mserv.gestionnaire_graphique.infoserv(None)
        self._le2mserv.gestionnaire_graphique.infoserv(u"Payed period: {}".format(
            selected_period))
        yield (self._le2mserv.gestionnaire_experience.finalize_part(
            "MarcheConcurrence", selected_period))

    @defer.inlineCallbacks
    def _display_payoffs(self):
        yield (self._le2mserv.gestionnaire_experience.run_step(
            u"Afficher les gains sur les postes", self._tous, "display_payoffs"))
