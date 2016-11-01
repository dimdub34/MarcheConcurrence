# -*- coding: utf-8 -*-

import logging
import random

from twisted.internet import defer
from twisted.spread import pb
from client.cltremote import IRemote
from client.cltgui.cltguidialogs import GuiRecapitulatif
import MarcheConcurrenceParams as pms
from MarcheConcurrenceGui import GuiDecision
import MarcheConcurrenceTexts as texts_MC


logger = logging.getLogger("le2m")


class RemoteMC(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self._histo_vars = [
            "MC_period", "MC_value_or_cost", "MC_transaction_price",
            "MC_periodpayoff", "MC_cumulativepayoff"]
        self._role = None
        self._value_or_cost = None

    @property
    def role(self):
        return self._role

    @property
    def value_or_cost(self):
        return self._value_or_cost

    def remote_configure(self, params, server_part, role):
        """
        Set the same parameters as in the server side
        :param params:
        :return:
        """
        logger.info(u"{} configure".format(self._le2mclt.uid))
        for k, v in params.viewitems():
            setattr(pms, k, v)
        self._server_part = server_part
        self._role = role
        self._histo.append(texts_MC.get_histo_head(self.role))

    def remote_newperiod(self, period):
        """
        Set the current period and delete the history
        :param period: the current period
        :return:
        """
        logger.info(u"{} Period {}".format(self._le2mclt.uid, period))
        self.currentperiod = period
        if self.currentperiod == 1:
            del self.histo[1:]

    def remote_display_decision(self, value_or_cost):
        """
        Display the decision screen
        :return: deferred
        """
        logger.info(u"{} Decision".format(self._le2mclt.uid))
        self._value_or_cost = value_or_cost
        if self._le2mclt.simulation:  # de pas simulation possible
            self.le2mclt.automatique = True
        defered = defer.Deferred()
        self._ecran_decision = GuiDecision(
            defered, self._le2mclt.automatique,
            self._le2mclt.screen, self.currentperiod, self.histo, self)
        self._ecran_decision.show()
        return defered

    def remote_display_summary(self, period_content):
        """
        Display the summary screen
        :param period_content: dictionary with the content of the current period
        :return: deferred
        """
        logger.info(u"{} Summary".format(self._le2mclt.uid))
        self.histo.append([period_content.get(k) for k in self._histo_vars])
        if self._le2mclt.simulation:
            return 1
        else:
            defered = defer.Deferred()
            ecran_recap = GuiRecapitulatif(
                defered, self._le2mclt.automatique, self._le2mclt.screen,
                self.currentperiod, self.histo,
                texts_MC.get_text_summary(period_content), size_histo=(600, 100))
            ecran_recap.show()
            return defered

    @defer.inlineCallbacks
    def send_offer(self, offer):
        """
        Lorsque le sujet fait une offre depuis son écran
        :param offer:
        :return:
        """
        yield (self._server_part.callRemote("set_offer", offer))

    @defer.inlineCallbacks
    def send_transaction(self, existing_offer):
        """
        Lorsque le sujet accepte la meilleure offre en cours ou fait une offre
        égale à la meilleure offre en cours
        :param existing_offer:
        :return:
        """
        yield (self._server_part.callRemote("set_transaction", existing_offer))

    def remote_add_offer(self, offer_dict):
        """
        Lorsque un des sujets du groupe (le sujet "sender" compris) a fait
        une offre
        :param offer_dict: un dictionnaire avec les propriétés de l'offre
        :return:
        """
        self._ecran_decision.add_offer(offer_dict,
                                       self.le2mclt.uid == offer_dict["MC_sender"])

    def remote_add_transaction(self, sell_offer, buy_offer):
        """
        Lorsque un des sujets du groupe (le sujet "sender" compris) a fait une
        transaction.
        :param sell_offer:
        :param buy_offer:
        :return:
        """
        concerned = self.le2mclt.uid in [sell_offer["MC_sender"],
                                         buy_offer["MC_sender"]]
        self._ecran_decision.add_transaction(sell_offer, buy_offer, concerned)

    def remote_display_role(self):
        if self.le2mclt.simulation:
            return 1
        else:
            return self.le2mclt.get_remote("base").remote_display_information(
                texts_MC.get_text_role(self._role))

    def remote_display_payoffs(self, payoff_infos):
        logger.debug(u"{} display_payoffs".format(self.le2mclt.uid))
        txt_payoff = texts_MC.get_text_payoff(payoff_infos)
        return self.le2mclt.get_remote("base").remote_display_information(
            txt_payoff)
