from datamodel import OrderDepth, TradingState, Order
from typing import List
import jsonpickle
import numpy as np
import math

# Définition des produits utilisés dans ta stratégie
class Product:
    KELP = "KELP"
    RAINFOREST_RESIN = "RAINFOREST_RESIN"
    SQUID_INK = "SQUID_INK"

# Paramètres de stratégie pour chacun de tes produits.
# Ces valeurs (fair_value, take_width, etc.) peuvent être ajustées en fonction des observations et tests.
PARAMS = {
    Product.KELP: {
        "fair_value": 50,          # Valeur estimée par défaut pour KELP
        "take_width": 1,
        "clear_width": 0,
        "disregard_edge": 1,
        "join_edge": 2,
        "default_edge": 4,
        "soft_position_limit": 10,
    },
    Product.RAINFOREST_RESIN: {
        "fair_value": 200,         # Valeur estimée par défaut pour RAINFOREST_RESIN
        "take_width": 1,
        "clear_width": 0,
        "prevent_adverse": True,   # Paramètre de gestion adverse
        "adverse_volume": 15,
        "reversion_beta": -0.229,  # Coefficient pour ajustement éventuel dynamique (non développé ici)
        "disregard_edge": 1,
        "join_edge": 0,
        "default_edge": 1,
    },
    Product.SQUID_INK: {
        "fair_value": 75,          # Valeur estimée par défaut pour SQUID_INK
        "take_width": 1,
        "clear_width": 0,
        "disregard_edge": 1,
        "join_edge": 2,
        "default_edge": 4,
        "soft_position_limit": 10,
    },
}

class Trader:
    def __init__(self, params=None):
        if params is None:
            params = PARAMS
        self.params = params
        # Limites de position pour chaque produit (ces valeurs sont indicatives et peuvent être ajustées)
        self.LIMIT = {
            Product.KELP: 50,
            Product.RAINFOREST_RESIN: 50,
            Product.SQUID_INK: 50,
        }
    
    def take_best_orders(
        self,
        product: str,
        fair_value: int,
        take_width: float,
        orders: List[Order],
        order_depth: OrderDepth,
        position: int,
        buy_order_volume: int,
        sell_order_volume: int,
        prevent_adverse: bool = False,
        adverse_volume: int = 0,
    ) -> (int, int):
        position_limit = self.LIMIT[product]

        # Traitement pour les sell_orders : possibilité d'achat
        if len(order_depth.sell_orders) != 0:
            best_ask = min(order_depth.sell_orders.keys())
            # Le volume est négatif, d'où la multiplication par -1 pour obtenir la quantité absolue
            best_ask_amount = -1 * order_depth.sell_orders[best_ask]

            if not prevent_adverse or abs(best_ask_amount) <= adverse_volume:
                if best_ask <= fair_value - take_width:
                    quantity = min(best_ask_amount, position_limit - position)
                    if quantity > 0:
                        orders.append(Order(product, best_ask, quantity))
                        buy_order_volume += quantity
                        order_depth.sell_orders[best_ask] += quantity
                        if order_depth.sell_orders[best_ask] == 0:
                            del order_depth.sell_orders[best_ask]

        # Traitement pour les buy_orders : possibilité de vente
        if len(order_depth.buy_orders) != 0:
            best_bid = max(order_depth.buy_orders.keys())
            best_bid_amount = order_depth.buy_orders[best_bid]
            if not prevent_adverse or abs(best_bid_amount) <= adverse_volume:
                if best_bid >= fair_value + take_width:
                    quantity = min(best_bid_amount, position_limit + position)
                    if quantity > 0:
                        orders.append(Order(product, best_bid, -quantity))
                        sell_order_volume += quantity
                        order_depth.buy_orders[best_bid] -= quantity
                        if order_depth.buy_orders[best_bid] == 0:
                            del order_depth.buy_orders[best_bid]
        return buy_order_volume, sell_order_volume

    def market_make(
        self,
        product: str,
        orders: List[Order],
        bid: int,
        ask: int,
        position: int,
        buy_order_volume: int,
        sell_order_volume: int,
    ) -> (int, int):
        # Calcule la quantité maximale qui peut être achetée sans dépasser la limite
        buy_quantity = self.LIMIT[product] - (position + buy_order_volume)
        if buy_quantity > 0:
            orders.append(Order(product, round(bid), buy_quantity))
        # Calcule la quantité maximale pouvant être vendue
        sell_quantity = self.LIMIT[product] + (position - sell_order_volume)
        if sell_quantity > 0:
            orders.append(Order(product, round(ask), -sell_quantity))
        return buy_order_volume, sell_order_volume

    def clear_position_order(
        self,
        product: str,
        fair_value: float,
        width: int,
        orders: List[Order],
        order_depth: OrderDepth,
        position: int,
        buy_order_volume: int,
        sell_order_volume: int,
    ) -> (int, int):
        position_after_take = position + buy_order_volume - sell_order_volume
        fair_for_bid = round(fair_value - width)
        fair_for_ask = round(fair_value + width)

        buy_quantity = self.LIMIT[product] - (position + buy_order_volume)
        sell_quantity = self.LIMIT[product] + (position - sell_order_volume)

        if position_after_take > 0:
            # Regroupe les volumes des buy_orders avec un prix supérieur à fair_for_ask
            clear_quantity = sum(
                volume
                for price, volume in order_depth.buy_orders.items()
                if price >= fair_for_ask
            )
            clear_quantity = min(clear_quantity, position_after_take)
            sent_quantity = min(sell_quantity, clear_quantity)
            if sent_quantity > 0:
                orders.append(Order(product, fair_for_ask, -abs(sent_quantity)))
                sell_order_volume += abs(sent_quantity)
        elif position_after_take < 0:
            # Regroupe les volumes des sell_orders avec un prix inférieur à fair_for_bid
            clear_quantity = sum(
                abs(volume)
                for price, volume in order_depth.sell_orders.items()
                if price <= fair_for_bid
            )
            clear_quantity = min(clear_quantity, abs(position_after_take))
            sent_quantity = min(buy_quantity, clear_quantity)
            if sent_quantity > 0:
                orders.append(Order(product, fair_for_bid, abs(sent_quantity)))
                buy_order_volume += abs(sent_quantity)
        return buy_order_volume, sell_order_volume

    def make_orders(
        self,
        product,
        order_depth: OrderDepth,
        fair_value: float,
        position: int,
        buy_order_volume: int,
        sell_order_volume: int,
        disregard_edge: float,
        join_edge: float,
        default_edge: float,
        manage_position: bool = False,
        soft_position_limit: int = 0,
    ):
        orders: List[Order] = []
        # Sélectionne les sell_orders au-dessus de (fair_value + disregard_edge)
        asks_above_fair = [
            price
            for price in order_depth.sell_orders.keys()
            if price > fair_value + disregard_edge
        ]
        # Sélectionne les buy_orders en-dessous de (fair_value - disregard_edge)
        bids_below_fair = [
            price
            for price in order_depth.buy_orders.keys()
            if price < fair_value - disregard_edge
        ]

        best_ask_above_fair = min(asks_above_fair) if asks_above_fair else None
        best_bid_below_fair = max(bids_below_fair) if bids_below_fair else None

        ask = round(fair_value + default_edge)
        if best_ask_above_fair is not None:
            if abs(best_ask_above_fair - fair_value) <= join_edge:
                ask = best_ask_above_fair  # Rejoint les ordres existants
            else:
                ask = best_ask_above_fair - 1  # Améliore légèrement (pennying)
                
        bid = round(fair_value - default_edge)
        if best_bid_below_fair is not None:
            if abs(fair_value - best_bid_below_fair) <= join_edge:
                bid = best_bid_below_fair
            else:
                bid = best_bid_below_fair + 1

        if manage_position:
            if position > soft_position_limit:
                ask -= 1
            elif position < -soft_position_limit:
                bid += 1

        buy_order_volume, sell_order_volume = self.market_make(
            product,
            orders,
            bid,
            ask,
            position,
            buy_order_volume,
            sell_order_volume,
        )

        return orders, buy_order_volume, sell_order_volume

    def take_orders(
        self,
        product: str,
        order_depth: OrderDepth,
        fair_value: float,
        take_width: float,
        position: int,
        prevent_adverse: bool = False,
        adverse_volume: int = 0,
    ) -> (List[Order], int, int):
        orders: List[Order] = []
        buy_order_volume = 0
        sell_order_volume = 0

        buy_order_volume, sell_order_volume = self.take_best_orders(
            product,
            fair_value,
            take_width,
            orders,
            order_depth,
            position,
            buy_order_volume,
            sell_order_volume,
            prevent_adverse,
            adverse_volume,
        )
        return orders, buy_order_volume, sell_order_volume

    def clear_orders(
        self,
        product: str,
        order_depth: OrderDepth,
        fair_value: float,
        clear_width: int,
        position: int,
        buy_order_volume: int,
        sell_order_volume: int,
    ) -> (List[Order], int, int):
        orders: List[Order] = []
        buy_order_volume, sell_order_volume = self.clear_position_order(
            product,
            fair_value,
            clear_width,
            orders,
            order_depth,
            position,
            buy_order_volume,
            sell_order_volume,
        )
        return orders, buy_order_volume, sell_order_volume

    def run(self, state: TradingState):
        # Récupération éventuelle de l'état précédent depuis traderData
        traderObject = {}
        if state.traderData is not None and state.traderData != "":
            traderObject = jsonpickle.decode(state.traderData)
        else:
            traderObject = {}
        
        result = {}

        # Parcours de chacun de tes produits
        for product in [Product.KELP, Product.RAINFOREST_RESIN, Product.SQUID_INK]:
            if product in self.params and product in state.order_depths:
                position = state.position.get(product, 0)
                fair_value = self.params[product]["fair_value"]
                # Pour RAINFOREST_RESIN, on pourrait implémenter une logique dynamique (ex : reversion)
                # ici nous gardons simplement la valeur prédéfinie.
                
                orders_total = []
                buy_order_volume = 0
                sell_order_volume = 0

                # Prise d'ordres en se basant sur le carnet (take_orders)
                take_orders, buy_order_volume, sell_order_volume = self.take_orders(
                    product,
                    state.order_depths[product],
                    fair_value,
                    self.params[product]["take_width"],
                    position,
                    self.params[product].get("prevent_adverse", False),
                    self.params[product].get("adverse_volume", 0),
                )

                # Nettoyage des positions (clear_orders)
                clear_orders, buy_order_volume, sell_order_volume = self.clear_orders(
                    product,
                    state.order_depths[product],
                    fair_value,
                    self.params[product]["clear_width"],
                    position,
                    buy_order_volume,
                    sell_order_volume,
                )

                # Mise en place d'ordres de market making (make_orders)
                make_orders, _, _ = self.make_orders(
                    product,
                    state.order_depths[product],
                    fair_value,
                    position,
                    buy_order_volume,
                    sell_order_volume,
                    self.params[product]["disregard_edge"],
                    self.params[product]["join_edge"],
                    self.params[product]["default_edge"],
                    manage_position=True,
                    soft_position_limit=self.params[product].get("soft_position_limit", 0),
                )

                orders_total.extend(take_orders)
                orders_total.extend(clear_orders)
                orders_total.extend(make_orders)
                
                result[product] = orders_total

        conversions = 0
        traderData = jsonpickle.encode(traderObject)
        return result, conversions, traderData
