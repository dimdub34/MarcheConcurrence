# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""

import logging
from PyQt4 import QtGui, QtCore
from twisted.internet import defer
from random import randint
from util.utili18n import le2mtrans
import MarcheConcurrenceParams as pms
from MarcheConcurrenceTexts import trans_MC
import MarcheConcurrenceTexts as texts_MC
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import WPeriod, WExplication, WCompterebours


logger = logging.getLogger("le2m")


class MyStandardItem(QtGui.QStandardItem):
    def __init__(self, value):
        QtGui.QStandardItem.__init__(self)
        self.__value = value
        self.setText(str(value))

    def __lt__(self, other):
        return other < self.__value

    def value(self):
        return self.__value


class GuiDecision(QtGui.QDialog):
    def __init__(self, defered, automatique, parent, period, historique, remote):
        super(GuiDecision, self).__init__(parent)

        # variables
        self._defered = defered
        self._automatique = automatique
        self._historique = GuiHistorique(self, historique)
        self._remote = remote
        self._offer_items = {}

        layout = QtGui.QVBoxLayout(self)

        wperiod = WPeriod(
            period=period, ecran_historique=self._historique)
        layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_MC.get_text_explanation(self._remote.role,
                                                self._remote.value_or_cost),
            size=(450, 50), parent=self)
        layout.addWidget(wexplanation)

        self._compte_rebours = WCompterebours(parent=self, temps=pms.TEMPS,
                                              actionfin=self._accept)
        layout.addWidget(self._compte_rebours)

        gridlayout = QtGui.QGridLayout()
        layout.addLayout(gridlayout)

        CURRENT_LINE = 0

        gridlayout.addWidget(QtGui.QLabel(u"Offres de ventes"), CURRENT_LINE, 0)
        gridlayout.addWidget(QtGui.QLabel(u"Offres d'achats"), CURRENT_LINE, 1)
        gridlayout.addWidget(QtGui.QLabel(u"Transactions"), CURRENT_LINE, 2)

        CURRENT_LINE += 1

        self._model_ventes = QtGui.QStandardItemModel()
        self._listview_ventes = QtGui.QListView()
        self._listview_ventes.setModel(self._model_ventes)
        self._listview_ventes.setMaximumSize(300, 600)
        gridlayout.addWidget(self._listview_ventes, CURRENT_LINE, 0)

        self._model_achats = QtGui.QStandardItemModel()
        self._listview_achats = QtGui.QListView()
        self._listview_achats.setModel(self._model_achats)
        self._listview_achats.setMaximumSize(300, 600)
        gridlayout.addWidget(self._listview_achats, CURRENT_LINE, 1)

        self._listwidget_transactions = QtGui.QListWidget()
        self._listwidget_transactions.setMaximumSize(300, 600)
        gridlayout.addWidget(self._listwidget_transactions, CURRENT_LINE, 2)

        CURRENT_LINE += 1

        if self._remote.role == pms.VENDEUR:

            self._layout_offer = QtGui.QHBoxLayout()
            self._layout_offer.addWidget(QtGui.QLabel(u"Offre de vente"))
            self._spin_offer = QtGui.QDoubleSpinBox()
            self._spin_offer.setDecimals(pms.DECIMALES)
            self._spin_offer.setMinimum(0)
            self._spin_offer.setMaximum(500)
            self._spin_offer.setButtonSymbols(QtGui.QSpinBox.NoButtons)
            self._spin_offer.setMaximumWidth(50)
            self._layout_offer.addWidget(self._spin_offer)
            self._button_send_offer = QtGui.QPushButton(u"Envoyer")
            self._button_send_offer.setMaximumWidth(100)
            self._button_send_offer.clicked.connect(lambda _: self._send_offer())
            self._layout_offer.addWidget(self._button_send_offer)
            self._layout_offer.addSpacerItem(
                QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                                  QtGui.QSizePolicy.Minimum))
            gridlayout.addLayout(self._layout_offer, CURRENT_LINE, 0)

        else:

            self._layout_offer = QtGui.QHBoxLayout()
            self._layout_offer.addWidget(QtGui.QLabel(u"Offre d'achat"))
            self._spin_offer = QtGui.QDoubleSpinBox()
            self._spin_offer.setDecimals(pms.DECIMALES)
            self._spin_offer.setMinimum(0)
            self._spin_offer.setMaximum(500)
            self._spin_offer.setButtonSymbols(QtGui.QSpinBox.NoButtons)
            self._spin_offer.setMaximumWidth(50)
            self._layout_offer.addWidget(self._spin_offer)
            self._button_send_offer = QtGui.QPushButton(u"Envoyer")
            self._button_send_offer.setMaximumWidth(100)
            self._button_send_offer.clicked.connect(lambda _: self._send_offer())
            self._layout_offer.addWidget(self._button_send_offer)
            self._layout_offer.addSpacerItem(
                QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                                  QtGui.QSizePolicy.Minimum))
            gridlayout.addLayout(self._layout_offer, CURRENT_LINE, 1)

        self.setWindowTitle(trans_MC(u"Marché"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if self._automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.setSingleShot(False)
            self._timer_automatique.timeout.connect(self._play_auto)
            self._timer_automatique.start(5000)
                
    def reject(self):
        pass
    
    def _accept(self):
        try:
            self._timer_automatique.stop()
        except AttributeError:
            pass
        self.accept()
        self._defered.callback(1)

    def _play_auto(self):
        """
        called by the timer when the program play automatically
        :return:
        """
        if self._remote.role == pms.ACHETEUR:
            self._spin_offer.setValue(randint(0, self._remote.value_or_cost))

        else:
            offer_min = self._remote.value_or_cost
            offer = 0

            if pms.TREATMENT == pms.TAXE_UNITE:
                offer = randint(offer_min + pms.TAXE_UNITE_MONTANT,
                                             max(pms.VALEURS) + 10)

            elif pms.TREATMENT == pms.TAXE_VALEUR:
                while offer < (offer_min + offer * pms.TAXE_VALEUR_MONTANT):
                    offer = randint(int(offer_min * pms.TAXE_VALEUR_MONTANT),
                                    max(pms.VALEURS) + 10)

            self._spin_offer.setValue(offer)

        self._button_send_offer.click()

    def _enable_offer(self, true_or_false):
        self._spin_offer.setEnabled(true_or_false)
        self._button_send_offer.setEnabled(true_or_false)
        # self._button_send_transaction.setEnabled(true_or_false)

    def _sort_list(self, the_model):
        if the_model is self._model_ventes:
            the_model.sort(0, QtCore.Qt.AscendingOrder)
        else:
            the_model.sort(0, QtCore.Qt.DescendingOrder)
        first_item = the_model.item(0, 0)
        try:
            first_item.setForeground(QtGui.QColor("blue"))
            for i in range(1, the_model.rowCount()):
                the_model.item(i, 0).setForeground(QtGui.QColor("black"))
        except AttributeError:
            pass

    @defer.inlineCallbacks
    def _send_offer(self):
        logger.debug("call of send_offer")

        offer = self._spin_offer.value()

        if self._remote.role == pms.ACHETEUR:

            if offer > self._remote.value_or_cost:
                QtGui.QMessageBox.warning(
                    self, u"Attention", u"Vous ne pouvez pas faire une offre "
                                        u"supérieure à {}.".format(
                        self._remote.value_or_cost))
                return

            if self._model_ventes.rowCount() > 0:
                best_offer = self._model_ventes.item(0, 0).value()
                if offer == best_offer:
                    yield (self._send_transaction(pms.OFFRE_VENTE))
                else:
                    yield (self._remote.send_offer(offer))
            else:
                yield (self._remote.send_offer(offer))

        else:

            offer_min = self._remote.value_or_cost

            if pms.TREATMENT == pms.TAXE_UNITE:
                offer_min += pms.TAXE_UNITE_MONTANT

            elif pms.TREATMENT == pms.TAXE_VALEUR:
                offer_min += offer * pms.TAXE_VALEUR_MONTANT

            if offer < offer_min:
                QtGui.QMessageBox.warning(
                    self, u"Attention", u"Vous ne pouvez pas faire une offre "
                                        u"inférieure à {}.".format(offer_min))
                return

            if self._model_achats.rowCount() > 0:
                best_offer = self._model_achats.item(0, 0).value()
                if offer == best_offer:
                    yield (self._send_transaction(pms.OFFRE_ACHAT))
                else:
                    yield (self._remote.send_offer(offer))
            else:
                yield (self._remote.send_offer(offer))

    @defer.inlineCallbacks
    def _send_transaction(self, achat_ou_vente):
        """
        Lorsque le sujet click sur le bouton accepter la meilleure offre actuelle
        :param achat_ou_vente:
        :return:
        """
        logger.debug("call of _send_transaction")

        if achat_ou_vente == pms.OFFRE_VENTE:
            if self._model_ventes.rowCount() == 0:
                return

            item = self._model_ventes.item(0, 0)
            offer = self._offer_items[item]

            if offer["MC_offer"] <= self._remote.value_or_cost:
                yield (self._remote.send_transaction(offer))

            else:
                if not self._automatique:
                    QtGui.QMessageBox.warning(
                        self, u"Attention", u"Vous ne pouvez accepter une offre "
                                            u"supérieure à {}.".format
                        (self._remote.value_or_cost))
                return

        else:
            if self._model_achats.rowCount() == 0:
                return

            item = self._model_achats.item(0, 0)
            offer = self._offer_items[item]

            if offer["MC_offer"] >= self._remote.value_or_cost:
                yield (self._remote.send_transaction(offer))

            else:
                if not self._automatique:
                    QtGui.QMessageBox.warning(
                        self, u"Attention", u"Vous ne pouvez accepter une offre "
                                            u"inférieure à {}.".format
                        (self._remote.value_or_cost))
                return

    def add_offer(self, offer, concerned):
        """
        Ajoute une offre sur la liste correspondante
        :param offer:
        :param concerned: si le sujet est à l'origine de l'offre
        :return:
        """
        logger.debug("add_offer: {}".format(offer))

        # on supprime les offres de celui qui vient de faire l'offre
        for v in self._offer_items.viewvalues():
            if v["MC_sender"] == offer["MC_sender"]:
                self.remove_offer(v)

        if offer["MC_type"] == pms.OFFRE_ACHAT:
            item = MyStandardItem(offer["MC_offer"])
            # self._model_achats.insertRow(0, item)
            self._model_achats.appendRow(item)
            self._sort_list(self._model_achats)

        else:
            item = MyStandardItem(offer["MC_offer"])
            # self._model_ventes.insertRow(0, item)
            self._model_ventes.appendRow(item)
            self._sort_list(self._model_ventes)

        self._offer_items[item] = offer

    def remove_offer(self, offer):
        """
        remove the offer from the corresponding list
        :param offer:
        :return:
        """
        logger.debug("call of remove_offer: {}".format(offer))
        for k, v in self._offer_items.viewitems():
            if offer == v:

                if offer["MC_type"] == pms.OFFRE_ACHAT:
                    for i in range(self._model_achats.rowCount()):
                        if self._model_achats.item(i, 0) == k:
                            self._model_achats.removeRow(i)
                            break
                    self._sort_list(self._model_achats)

                elif offer["MC_type"] == pms.OFFRE_VENTE:
                    for i in range(self._model_ventes.rowCount()):
                        if self._model_ventes.item(i, 0) == k:
                            self._model_ventes.removeRow(i)
                            break
                    self._sort_list(self._model_ventes)

    def add_transaction(self, sell_offer, buy_offer, concerned):
        """
        :param sell_offer:
        :param buy_offer:
        :return:
        """
        item = QtGui.QListWidgetItem(self._listwidget_transactions)
        item.setText(u"{}".format(sell_offer["MC_offer"]))

        if concerned:
            item.setForeground(QtGui.QColor("green"))
            self._enable_offer(False)
            try:
                self._timer_automatique.stop()
            except AttributeError:
                pass

        self.remove_offer(sell_offer)
        self.remove_offer(buy_offer)

        # on supprime aussi toutes les offres concernant les sujets impliqués
        # dans la transaction
        for v in self._offer_items.viewvalues():
            if v["MC_sender"] == sell_offer["MC_sender"] or \
                            v["MC_sender"] == buy_offer["MC_sender"]:
                self.remove_offer(v)


class DConfigure(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        form = QtGui.QFormLayout()
        layout.addLayout(form)

        # treatment
        self._combo_treatment = QtGui.QComboBox()
        self._combo_treatment.addItems(list(sorted(pms.TREATMENTS_NAMES.viewvalues())))
        self._combo_treatment.setCurrentIndex(pms.TREATMENT)
        form.addRow(QtGui.QLabel(u"Traitement"), self._combo_treatment)
        
        # nombre de périodes
        self._spin_periods = QtGui.QSpinBox()
        self._spin_periods.setMinimum(0)
        self._spin_periods.setMaximum(100)
        self._spin_periods.setSingleStep(1)
        self._spin_periods.setValue(pms.NOMBRE_PERIODES)
        self._spin_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_periods.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Nombre de périodes"), self._spin_periods)

        # periode essai
        self._checkbox_essai = QtGui.QCheckBox()
        self._checkbox_essai.setChecked(pms.PERIODE_ESSAI)
        form.addRow(QtGui.QLabel(u"Période d'essai"), self._checkbox_essai)
        
        # taille groupes
        self._spin_groups = QtGui.QSpinBox()
        self._spin_groups.setMinimum(2)
        self._spin_groups.setMaximum(100)
        self._spin_groups.setSingleStep(1)
        self._spin_groups.setValue(pms.TAILLE_GROUPES)
        self._spin_groups.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_groups.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Taille des groupes"), self._spin_groups)

        # temps de marché
        self._timeEdit = QtGui.QTimeEdit()
        self._timeEdit.setDisplayFormat("hh:mm:ss")
        self._timeEdit.setTime(QtCore.QTime(pms.TEMPS.hour,
                                            pms.TEMPS.minute,
                                            pms.TEMPS.second))
        self._timeEdit.setMaximumWidth(100)
        form.addRow(QtGui.QLabel(u"Durée du marché"), self._timeEdit)


        button = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        button.accepted.connect(self._accept)
        button.rejected.connect(self.reject)
        layout.addWidget(button)

        self.setWindowTitle(u"Configurer")
        self.adjustSize()
        self.setFixedSize(self.size())

    def _accept(self):
        pms.TREATMENT = self._combo_treatment.currentIndex()
        pms.PERIODE_ESSAI = self._checkbox_essai.isChecked()
        pms.TEMPS = self._timeEdit.time().toPyTime()
        pms.NOMBRE_PERIODES = self._spin_periods.value()
        pms.TAILLE_GROUPES = self._spin_groups.value()
        self.accept()
