"""
strategies/rainforest_resin/scalping.py
Stratégie de scalping pour le produit Rainforest Resin.
"""

from models.datamodel import Order, TradingState
from utils import calculate_imbalance

class RainforestResinScalping:
    def __init__(self):
        # Vous pouvez initialiser ici des variables propres à la stratégie
        self.last_signal = None

    def compute_orders(self, state: TradingState, product: str):
        orders = []
        order_depth = state.order_depths[product]
        
        # Exemple de calcul d'un prix acceptable à partir du scalping
        acceptable_price = self.compute_acceptable_price(state, product)
        
        # Exemple simple : si le meilleur ask est inférieur au prix acceptable, acheter
        if order_depth.sell_orders:
            # Trier les clés pour obtenir le meilleur prix ask (le plus bas)
            best_ask = sorted(order_depth.sell_orders.keys())[0]
            if best_ask < acceptable_price:
                quantity = -order_depth.sell_orders[best_ask]  # Conversion en quantité positive pour l'achat
                orders.append(Order(product, best_ask, quantity))
        
        # De même, si le meilleur bid est supérieur au prix acceptable, vendre
        if order_depth.buy_orders:
            best_bid = sorted(order_depth.buy_orders.keys(), reverse=True)[0]
            if best_bid > acceptable_price:
                quantity = -order_depth.buy_orders[best_bid]  # La logique peut varier selon vos besoins
                orders.append(Order(product, best_bid, quantity))
                
        # Ici, vous pouvez affiner la logique en fonction de l'imbalance, des micro-fluctuations, etc.
        imbalance = calculate_imbalance(order_depth)
        # Vous pouvez ajouter d'autres conditions et ajuster le nombre d'ordres selon le signal

        return orders

    def compute_acceptable_price(self, state: TradingState, product: str):
        # Implémentez ici votre logique propre au scalping pour déterminer le prix acceptable.
        # Par exemple, en prenant en compte le mid_price, l'imbalance, et d'autres indicateurs.
        # Ce code est un simple placeholder.
        return 10  # Valeur à remplacer par le calcul réel
