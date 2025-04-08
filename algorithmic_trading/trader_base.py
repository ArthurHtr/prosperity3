"""
trader_base.py
Implémentation de la classe Trader qui respecte le squelette requis.
Elle centralise l'exécution et délègue à des stratégies spécifiques par produit.
"""

import json
from models.datamodel import TradingState, Order

from strategies.RAINFOREST_RESIN.scalping import RainforestResinScalping

class Trader:
    def __init__(self):
        # Dictionnaire associant chaque produit à sa stratégie
        self.strategies = {
            "RAINFOREST_RESIN": RainforestResinScalping(),
        }
        
        # Variable pour stocker l'état entre les itérations si besoin (via traderData)
        self.trader_state = {}

    def run(self, state: TradingState):
        result = {}

        # Parcourir chaque produit présent dans l'état (ordre book)
        for product in state.order_depths:
            if product in self.strategies:
                strategy = self.strategies[product]
                # Chaque stratégie doit exposer une méthode compute_orders qui retourne une liste d'ordres
                orders = strategy.compute_orders(state, product)
                result[product] = orders
            else:
                # Si aucune stratégie spécifique n'est définie, on peut ignorer ou appliquer une règle par défaut
                result[product] = []

        # Exemple simple de gestion d'état (traderData)
        traderData = json.dumps(self.trader_state)
        conversions = 0  # Vous pouvez intégrer la logique des conversions ici si nécessaire

        return result, conversions, traderData