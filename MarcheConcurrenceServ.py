# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
from twisted.internet import defer
from random import choice
from util import utiltools
from util.utili18n import le2mtrans
import MarcheConcurrenceParams as pms


logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur(object):
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv

        # creation of the menu (will be placed in the "part" menu on the
        # server screen)
        actions = OrderedDict()
        actions[le2mtrans(u"Configure")] = self._configure
        actions[le2mtrans(u"Display parameters")] = \
            lambda _: self._le2mserv.gestionnaire_graphique. \
            display_information2(
                utiltools.get_module_info(pms), le2mtrans(u"Parameters"))
        actions[le2mtrans(u"Start")] = lambda _: self._demarrer()
        actions[le2mtrans(u"Display payoffs")] = \
            lambda _: self._le2mserv.gestionnaire_experience.\
            display_payoffs_onserver("MarcheConcurrence")
        self._le2mserv.gestionnaire_graphique.add_topartmenu(
            u"Marché Taxation - Concurrence", actions)

    def _configure(self):
        self._le2mserv.gestionnaire_graphique.display_information(
            le2mtrans(u"There is no parameter to configure"))
        return

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
            "MarcheConcurrence", "PartieMC",
            "RemoteMC", pms))
        self._tous = self._le2mserv.gestionnaire_joueurs.get_players(
            'MarcheConcurrence')

        # form groups ----------------------------------------------------------
        if pms.TAILLE_GROUPES > 0:
            try:
                self._le2mserv.gestionnaire_groupes.former_groupes(
                    self._le2mserv.gestionnaire_joueurs.get_players(),
                    pms.TAILLE_GROUPES, forcer_nouveaux=True)
            except ValueError as e:
                self._le2mserv.gestionnaire_graphique.display_error(
                    e.message)
                return

        # set group comp -------------------------------------------------------
        for num, comp in self._le2mserv.gestionnaire_groupes.get_groupes(
                "MarcheConcurrence").viewitems():
            for i in comp:
                setattr(i.joueur, "group_comp", comp)

        # set roles ------------------------------------------------------------
        self._le2mserv.gestionnaire_graphique.infoserv(u"*** Roles ***")
        for num, comp in self._le2mserv.gestionnaire_groupes.get_groupes().viewitems():
            for j in comp[: pms.TAILLE_GROUPES/2]:
                setattr(j, "role", pms.ACHETEUR)
            for k in comp[pms.TAILLE_GROUPES/2:]:
                setattr(k, "role", pms.VENDEUR)
            self._le2mserv.gestionnaire_graphique.infoserv(
                u"G{} - Buyers: {}".format(num.split("_")[2],
                                           comp[:pms.TAILLE_GROUPES/2]))
            self._le2mserv.gestionnaire_graphique.infoserv(
                u"G{} - Sellers: {}".format(num.split("_")[2],
                                            comp[pms.TAILLE_GROUPES / 2:]))

        # configure remotes ----------------------------------------------------
        # se fait à cet endroit car la part envoie le role au remote
        yield (self._le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Configure"), self._tous, "configure"))

        # Start repetitions ====================================================
        for period in range(1 if pms.NOMBRE_PERIODES else 0,
                        pms.NOMBRE_PERIODES + 1):

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
        yield (self._le2mserv.gestionnaire_experience.finalize_part(
            "MarcheConcurrence"))
