"""
utils.py
Contient les fonctions utilitaires communes, par exemple pour calculer des indicateurs,
gérer la sérialisation ou d'autres fonctions récurrentes dans votre algo.
"""

def calculate_imbalance(order_depth):
    """
    Calcule l'imbalance (déséquilibre) entre les volumes d'achat et de vente.
    """
    total_bid = sum(order_depth.buy_orders.values())
    total_ask = abs(sum(order_depth.sell_orders.values()))
    if total_bid + total_ask == 0:
        return 0
    imbalance = (total_bid - total_ask) / (total_bid + total_ask)
    return imbalance
