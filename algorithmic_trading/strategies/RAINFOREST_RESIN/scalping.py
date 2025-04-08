"""
strategies/rainforest_resin/scalping.py
Stratégie de scalping pour le produit Rainforest Resin.
"""

from models.datamodel import Order, TradingState
from utils import calculate_imbalance

class RainforestResinScalping:
    def __init__(self):
        # On définit ici la limite de position pour RAINFOREST_RESIN (exemple : 10 unités)
        self.position_limit = 50

    def get_fair_value(self, state: TradingState, product: str) -> int:
        """
        Retourne la fair value pour RAINFOREST_RESIN.
        Ici, on fixe statiquement à 100 (à adapter selon votre calcul et vos indicateurs).
        """
        return 100

    def compute_orders(self, state: TradingState, product: str):
        """
        Calcule et retourne une liste d'ordres pour RAINFOREST_RESIN.
        """
        orders = []
        order_depth = state.order_depths.get(product)
        if order_depth is None:
            return orders

        # Récupération de la position actuelle pour le produit et calcul de la fair value
        current_position = state.position.get(product, 0)
        fair_value = self.get_fair_value(state, product)

        # Affichage de quelques informations pour le débuggage
        print(f"Produit: {product} | Position actuelle: {current_position} | Fair value: {fair_value}")
        print(f"Buy orders: {order_depth.buy_orders} | Sell orders: {order_depth.sell_orders}")

        # ------------------------
        # Opportunité d'achat
        # ------------------------
        if order_depth.sell_orders:
            # Le meilleur prix de vente est le plus bas
            best_sell_price = min(order_depth.sell_orders.keys())
            if best_sell_price < fair_value:
                # Quantité totale disponible sur les niveaux de vente à un prix inférieur ou égal à la fair value
                available_sell_qty = sum(abs(q) for price, q in order_depth.sell_orders.items() if price <= fair_value)
                # Calcul de la quantité autorisée afin de ne pas dépasser la limite de position
                allowed_buy_qty = self.position_limit - current_position
                buy_qty = min(available_sell_qty, allowed_buy_qty)
                print(f"Opportunité d'achat détectée au prix {best_sell_price} pour une quantité {buy_qty}")
                if buy_qty > 0:
                    orders.append(Order(product, best_sell_price, buy_qty))

        # ------------------------
        # Opportunité de vente
        # ------------------------
        if order_depth.buy_orders:
            # Le meilleur prix d'achat est le plus haut
            best_buy_price = max(order_depth.buy_orders.keys())
            if best_buy_price > fair_value:
                # Quantité totale disponible sur les niveaux d'achat à un prix supérieur ou égal à la fair value
                available_buy_qty = sum(q for price, q in order_depth.buy_orders.items() if price >= fair_value)
                # Pour une vente, la quantité maximale vendable est telle que la position short ne dépasse pas la limite.
                allowed_sell_qty = current_position + self.position_limit
                sell_qty = min(available_buy_qty, allowed_sell_qty)
                print(f"Opportunité de vente détectée au prix {best_buy_price} pour une quantité {sell_qty}")
                if sell_qty > 0:
                    # Un ordre de vente s'exprime par une quantité négative
                    orders.append(Order(product, best_buy_price, -sell_qty))

        # On peut aussi utiliser l'indicateur imbalance pour ajuster la stratégie (exemple de debug)
        imbalance = calculate_imbalance(order_depth)
        print(f"Imbalance calculée: {imbalance}")

        return orders