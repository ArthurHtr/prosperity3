# traders/sample_trader.py
from models.datamodel import TradingState, Order
from typing import List


class SimpleTrader:

    def run(self, state: TradingState):
        """
        Stratégie simple basée sur le carnet d'ordres :
         - Calcule le mid price à partir du meilleur bid et du meilleur ask.
         - Utilise une valeur de référence fixe (ex. 10 000) pour décider de rentrer en position long ou short.
         - Si on est long et le mid price dépasse la référence, on vend toute la position.
         - Si on est short et le mid price est inférieur à la référence, on rachète pour couvrir.
        """
        result = {}

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            orders: List[Order] = []

            # Si le carnet est vide pour l'une des faces, ne rien faire.
            if not order_depth.buy_orders or not order_depth.sell_orders:
                result[product] = orders
                continue

            best_bid = max(order_depth.buy_orders.keys())
            best_ask = min(order_depth.sell_orders.keys())
            mid_price = (best_bid + best_ask) / 2

            # Valeur de référence fixe (à ajuster selon le produit/marché)
            reference_price = 10000

            # La strategie actuelle ne fait que réagir, elle ne place pas d'ordres elle meme.
            pos = state.position.get(product, 0)
            if pos == 0:
                # Pas de position : 
                if mid_price < reference_price:
                    # Le marché est "bon marché" : entrée longue en achetant 1 unité au meilleur ask.
                    orders.append(Order(product, best_ask, 1))
                elif mid_price > reference_price:
                    # Le marché est "cher" : entrée short en vendant 1 unité (quantité négative) au meilleur bid.
                    orders.append(Order(product, best_bid, -1))

            elif pos > 0:
                # Déjà en long : sortir (vendre toute la position) si le mid dépasse la référence.
                if mid_price >= reference_price:
                    orders.append(Order(product, best_bid, -pos))
            elif pos < 0:
                # Déjà en short : couvrir (acheter pour réduire la position short) si le mid est inférieur à la référence.
                if mid_price <= reference_price:
                    orders.append(Order(product, best_ask, -pos))
            result[product] = orders


        traderData = "SIMPLE_STRATEGY"
        conversions = 0
        return result, conversions, traderData