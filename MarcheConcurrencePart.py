# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from twisted.internet import defer
from twisted.spread import pb
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, ForeignKey, String
from random import randint
from server.servbase import Base
from server.servparties import Partie
from util.utiltools import get_module_attributes
import MarcheConcurrenceParams as pms


logger = logging.getLogger("le2m")


class PartieMC(Partie, pb.Referenceable):
    __tablename__ = "partie_MarcheConcurrence"
    __mapper_args__ = {'polymorphic_identity': 'MarcheConcurrence'}
    partie_id = Column(Integer, ForeignKey('parties.id'), primary_key=True)
    repetitions = relationship('RepetitionsMC')

    def __init__(self, le2mserv, joueur):
        super(PartieMC, self).__init__(
            nom="MarcheConcurrence", nom_court="MC",
            joueur=joueur, le2mserv=le2mserv)
        self._current_sequence = None
        self.MC_gain_ecus = 0
        self.MC_gain_euros = 0
        if not hasattr(self.joueur, "payoff_infos"):
           setattr(self.joueur, "payoff_infos", dict())

    @defer.inlineCallbacks
    def configure(self, current_sequence):
        """
        On envoie aussi cet instance car le remote a besoin d'envoyer des
        offres et d'informer des offres qu'il accepte
        :return:
        """
        logger.debug(u"{} Configure".format(self.joueur))
        self._current_sequence = current_sequence
        yield (self.remote.callRemote("configure", get_module_attributes(pms),
                                      self))
        self.joueur.info(u"Ok")

    @defer.inlineCallbacks
    def newperiod(self, period):
        """
        Create a new period and inform the remote
        If this is the first period then empty the historic
        :param periode:
        :return:
        """
        logger.debug(u"{} New Period".format(self.joueur))
        self.currentperiod = RepetitionsMC(period)
        self.currentperiod.MC_sequence = self._current_sequence
        self.currentperiod.MC_group = self.joueur.groupe
        self.currentperiod.MC_role = self.joueur.role
        self.le2mserv.gestionnaire_base.ajouter(self.currentperiod)
        self.repetitions.append(self.currentperiod)
        yield (self.remote.callRemote("newperiod", period))
        logger.info(u"{} Ready for period {}".format(self.joueur, period))

    @defer.inlineCallbacks
    def display_decision(self):
        """
        Display the decision screen on the remote
        :return:
        """
        logger.debug(u"{} Decision".format(self.joueur))
        yield(self.remote.callRemote("display_decision",
                                     self.currentperiod.MC_value_or_cost))
        self.joueur.info(u"Ok")
        self.joueur.remove_waitmode()

    def compute_periodpayoff(self):
        """
        Compute the payoff for the period
        :return:
        """
        logger.debug(u"{} Period Payoff".format(self.joueur))
        self.currentperiod.MC_periodpayoff = 0

        if self.currentperiod.MC_transaction_price is not None:  # transaction

            self.currentperiod.MC_transaction_prime = pms.FORFAIT_TRANSACTION
            self.currentperiod.MC_periodpayoff = \
                self.currentperiod.MC_transaction_prime

            if self.joueur.role == pms.ACHETEUR:
                self.currentperiod.MC_periodpayoff += \
                    self.currentperiod.MC_value_or_cost - \
                    self.currentperiod.MC_transaction_price

            else:  # vendeur
                self.currentperiod.MC_periodpayoff += \
                self.currentperiod.MC_transaction_price - \
                self.currentperiod.MC_value_or_cost

                if pms.TREATMENT == pms.TAXE_UNITE:
                    self.currentperiod.MC_transaction_taxe = \
                        pms.TAXE_UNITE_MONTANT
                    self.currentperiod.MC_periodpayoff -= \
                        self.currentperiod.MC_transaction_taxe

                elif pms.TREATMENT == pms.TAXE_VALEUR:
                    self.currentperiod.MC_transaction_taxe = \
                    self.currentperiod.MC_transaction_price * \
                        pms.TAXE_VALEUR_MONTANT
                    self.currentperiod.MC_periodpayoff -= \
                        self.currentperiod.MC_transaction_taxe

        # cumulative payoff since the first period
        if self.currentperiod.MC_period < 2:
            self.currentperiod.MC_cumulativepayoff = \
                self.currentperiod.MC_periodpayoff
        else: 
            previousperiod = self.periods[self.currentperiod.MC_period - 1]
            self.currentperiod.MC_cumulativepayoff = \
                previousperiod.MC_cumulativepayoff + \
                self.currentperiod.MC_periodpayoff

        # we store the period in the self.periodes dictionnary
        self.periods[self.currentperiod.MC_period] = self.currentperiod

        logger.debug(u"{} Period Payoff {}".format(
            self.joueur,
            self.currentperiod.MC_periodpayoff))

    @defer.inlineCallbacks
    def display_summary(self, *args):
        """
        Send a dictionary with the period content values to the remote.
        The remote creates the text and the history
        :param args:
        :return:
        """
        logger.debug(u"{} Summary".format(self.joueur))
        yield(self.remote.callRemote(
            "display_summary", self.currentperiod.todict()))
        self.joueur.info("Ok")
        self.joueur.remove_waitmode()

    def compute_partpayoff(self, selected_period):
        """
        Compute the payoff for the part and set it on the remote.
        The remote stores it and creates the corresponding text for display
        (if asked)
        :return:
        """
        logger.debug(u"{} Part Payoff".format(self.joueur))

        self.MC_gain_ecus = self.periods[selected_period].MC_periodpayoff
        self.MC_gain_euros = self.MC_gain_ecus * pms.TAUX_CONVERSION

        self.joueur.payoff_infos[self._current_sequence] = {
            "period": selected_period, "gain_ecus": self.MC_gain_ecus,
            "gain_euros": self.MC_gain_euros}

        self.joueur.get_part("base").paiementFinal += self.MC_gain_euros

        logger.info(u'{} Period: {} Payoff ecus {} Payoff euros {:.2f}'.format(
            self.joueur, selected_period, self.MC_gain_ecus, self.MC_gain_euros))

    def create_offer(self, the_time, sender, sender_group, offer_type,
                     offer_amount):
        """
        Creation de l'offre dans la base de données
        :param the_time:
        :param sender:
        :param sender_group:
        :param offer_type:
        :param offer_amount:
        :return:
        """
        new_offer = OffersMC(
            the_time, sender, sender_group, offer_type, offer_amount)
        # on enregistre dans la base uniquement si c'est le joueur à l'origine
        # de l'offre, afin de ne pas enregistrer 50 fois la même offre
        if sender == self.joueur.uid:
            self.currentperiod.MC_offers.append(new_offer)
        return new_offer

    @defer.inlineCallbacks
    def remote_set_offer(self, offer):
        """
        Le sujet fait une offre de vente ou d'achat
        :param offer:
        :return:
        """
        logger.debug("call of set_offer: {}".format(offer))
        if self.currentperiod.MC_transaction_price is not None:
            return

        now = datetime.now()
        offer_infos = (now.strftime("%Y%m%d-%H:%M:%S"), self.joueur.uid,
                       self.joueur.groupe,
                       pms.OFFRE_ACHAT if self.joueur.role == pms.ACHETEUR else pms.OFFRE_VENTE,
                       offer)

        # creation de l'offre chez le joueur
        new_offer = self.create_offer(*offer_infos)
        self.joueur.info(u"offer {} {}".format(
            u"BUY" if self.joueur.role == pms.ACHETEUR else u"SELL",
            new_offer.MC_offer))

        # envoi de l'offre sur les remote des membres du groupe
        new_offer_dict = new_offer.todict()
        for j in self.joueur.group_composition:
            yield (j.get_part(self.nom).remote.callRemote("add_offer", new_offer_dict))

    @defer.inlineCallbacks
    def remote_set_transaction(self, existing_offer):
        """
        Le sujet a accepté une offre de vente ou d'achat
        Une transaction a donc lieu.
        :param offer:
        :return:
        """
        logger.debug("call of set_transaction: {}".format(existing_offer))

        # on verifie que l'offre existante n'a pas déjà été prise
        player_existing_offer = self.le2mserv.gestionnaire_joueurs.get_joueur(
            existing_offer["MC_sender"])
        if player_existing_offer.get_part(self.nom).currentperiod.MC_transaction_price is not None:
            defer.returnValue(0)

        # si le sujet a déjà fait une transaction on rejette
        if self.currentperiod.MC_transaction_price is not None:
            defer.returnValue(0)

        # d'abord on crée une offre
        now = datetime.now()
        offer_infos = (now.strftime("%Y%m%d-%H:%M:%S"), self.joueur.uid,
                       self.joueur.groupe,
                       pms.OFFRE_ACHAT if self.joueur.role == pms.ACHETEUR else pms.OFFRE_VENTE,
                       existing_offer["MC_offer"])

        # creation de l'offre chez le joueur
        new_offer = self.create_offer(*offer_infos)
        self.joueur.info(u"offer {} {}".format(
            u"BUY" if self.joueur.role == pms.ACHETEUR else u"SELL",
            new_offer.MC_offer))

        # creation de la transaction chez le joueur et l'autre joueur impliqué
        self.currentperiod.MC_transaction_price = new_offer.MC_offer
        for j in self.joueur.group_composition:
            if j.uid == existing_offer["MC_sender"]:
                j.get_part(self.nom).currentperiod.MC_transaction_price = \
                    existing_offer["MC_offer"]
                self.le2mserv.gestionnaire_graphique.infoserv(
                    u"G{} - {} with {} - price {}".format(
                        self.joueur.groupe.split("_")[2], self.joueur, j,
                        new_offer.MC_offer))

        # envoi de la transaction sur les remote des membres du groupe
        for j in self.joueur.group_composition:
            yield (j.get_part(self.nom).remote.callRemote("add_transaction",
                                       existing_offer, new_offer.todict()))
        defer.returnValue(1)

    @defer.inlineCallbacks
    def display_role(self):
        yield (self.remote.callRemote("display_role", self.joueur.role))
        self.joueur.info(u"Ok")
        self.joueur.remove_waitmode()

    @defer.inlineCallbacks
    def display_payoffs(self):
        yield (self.remote.callRemote("display_payoffs",
                                      self.joueur.payoff_infos))
        self.joueur.info(u"Ok")
        self.joueur.remove_waitmode()


class RepetitionsMC(Base):
    __tablename__ = 'partie_MarcheConcurrence_repetitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    partie_partie_id = Column(
        Integer,
        ForeignKey("partie_MarcheConcurrence.partie_id"))
    MC_offers = relationship('OffersMC')

    MC_sequence = Column(Integer)
    MC_period = Column(Integer)
    MC_treatment = Column(Integer)
    MC_group = Column(Integer)
    MC_role = Column(Integer)
    MC_value_or_cost = Column(Integer)
    MC_transaction_price = Column(Float)
    MC_transaction_prime = Column(Integer)
    MC_transaction_taxe = Column(Float)
    MC_periodpayoff = Column(Float)
    MC_cumulativepayoff = Column(Float)

    def __init__(self, period):
        self.MC_treatment = pms.TREATMENT
        self.MC_period = period
        self.MC_transaction_price = None
        self.MC_transaction_prime = 0
        self.MC_transaction_taxe = 0
        self.MC_decisiontime = 0
        self.MC_periodpayoff = 0
        self.MC_cumulativepayoff = 0

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if joueur:
            temp["joueur"] = joueur
        return temp


class OffersMC(Base):
    __tablename__ = 'partie_MarcheConcurrence_repetitions_offers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(Integer,
                            ForeignKey("partie_MarcheConcurrence_repetitions.id"))

    MC_time = Column(String)
    MC_sender = Column(String)
    MC_sender_group = Column(String)
    MC_type = Column(Integer)
    MC_offer = Column(Float)

    def __init__(self, time, sender, sender_group, type, offer):
        self.MC_time = time
        self.MC_sender = sender
        self.MC_sender_group = sender_group
        self.MC_type = type
        self.MC_offer = offer

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}