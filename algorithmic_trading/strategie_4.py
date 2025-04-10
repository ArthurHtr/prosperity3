from datamodel import OrderDepth, TradingState, Order, Trade
from typing import List, Dict, Tuple
import jsonpickle
import math

##############################################
# Fonction d'assistance pour calculer un profit simple
##############################################
def compute_profit(trades: List[Trade]) -> float:
    """
    Calcule un profit cumulatif naïf à partir de la liste des trades.
    Pour chaque trade, on considère que l'achat (quantité positive) génère un flux négatif
    et la vente (quantité négative) un flux positif.
    """
    profit = 0
    for t in trades:
        profit += -(t.price * t.quantity)
    return profit

##############################################
# Classe de base pour la stratégie par produit
##############################################
class ProductStrategy:
    def __init__(self, product: str, params: Dict, position_limit: int):
        self.product = product
        self.params = params
        self.position_limit = position_limit  # Ici, 50 pour tous
        # L'état interne sera stocké dans traderData (par exemple, l'historique des mid prices)
        self.internal_state = {}

    def compute_mid_price(self, order_depth: OrderDepth, fallback: float) -> float:
        """
        Calcule le mid price comme la moyenne entre le meilleur bid et le meilleur ask.
        Si l'un des deux n'est pas disponible, retourne fallback.
        """
        if order_depth.buy_orders and order_depth.sell_orders:
            best_bid = max(order_depth.buy_orders.keys())
            best_ask = min(order_depth.sell_orders.keys())
            mid = (best_bid + best_ask) / 2.0
            print(f"[{self.product}] Best Bid: {best_bid}, Best Ask: {best_ask}, Calculated Mid: {mid}")
            return mid
        print(f"[{self.product}] Données incomplètes dans le carnet. Fallback utilisé: {fallback}")
        return fallback

    def update_history(self, trader_state: Dict, mid_price: float) -> List[float]:
        """
        Met à jour l'historique des mid prices pour ce produit dans trader_state.
        On conserve ici les 30 dernières valeurs.
        """
        history = trader_state.get("history", [])
        history.append(mid_price)
        if len(history) > 30:
            history = history[-30:]
        trader_state["history"] = history
        print(f"[{self.product}] Historique mis à jour: {history[-3:]} ... (taille: {len(history)})")
        return history

    def rolling_average(self, history: List[float]) -> float:
        if history:
            avg = sum(history) / len(history)
            print(f"[{self.product}] Moyenne historique calculée: {avg}")
            return avg
        return 0.0

    def rolling_std(self, history: List[float], avg: float) -> float:
        if len(history) > 1:
            std = math.sqrt(sum((x - avg) ** 2 for x in history) / (len(history) - 1))
            print(f"[{self.product}] Ecart-type calculé: {std}")
            return std
        return 0.0

    def allowed_buy_quantity(self, position: int) -> int:
        qty = self.position_limit - position
        print(f"[{self.product}] Quantité max à acheter autorisée: {qty}")
        return qty

    def allowed_sell_quantity(self, position: int) -> int:
        qty = self.position_limit + position
        print(f"[{self.product}] Quantité max à vendre autorisée: {qty}")
        return qty

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        """
        Par défaut, la stratégie applique la logique basique.
        Les classes dérivées peuvent surcharger cette méthode.
        """
        orders = []
        default_fair = self.params.get("fair_value", 100)
        fair_value = self.compute_mid_price(order_depth, default_fair)
        orders.extend(self.basic_orders(fair_value, order_depth, position))
        return orders, trader_state

    def basic_orders(self, fair_value: float, order_depth: OrderDepth, position: int) -> List[Order]:
        """
        Logique simple : Si le meilleur ask est inférieur à fair_value, on passe un ordre d'achat ;
        si le meilleur bid est supérieur à fair_value, on passe un ordre de vente.
        """
        orders = []
        if order_depth.sell_orders:
            best_ask = min(order_depth.sell_orders.keys())
            if best_ask < fair_value:
                qty = self.allowed_buy_quantity(position)
                if qty > 0:
                    orders.append(Order(self.product, best_ask, qty))
                    print(f"[{self.product}] Basic BUY order: {qty} à {best_ask}")
        if order_depth.buy_orders:
            best_bid = max(order_depth.buy_orders.keys())
            if best_bid > fair_value:
                qty = self.allowed_sell_quantity(position)
                if qty > 0:
                    orders.append(Order(self.product, best_bid, -qty))
                    print(f"[{self.product}] Basic SELL order: {qty} à {best_bid}")
        return orders


##############################################
# Stratégie pour RAINFOREST_RESIN (Market Making / Scalping)
##############################################
class RainforestResinStrategy(ProductStrategy):
    def __init__(self, params: Dict):
        # Prix de base = 10000, position_limit = 50 pour RAINFOREST_RESIN
        super().__init__("RAINFOREST_RESIN", params, position_limit=50)
        # Paramètres de la stratégie
        self.base_offset = self.params.get("scalping_offset", 1)  # Offset de base
        self.volatility_coeff = self.params.get("volatility_coeff", 0.1)  # Coefficient pour ajuster l'offset avec la volatilité
        self.inventory_skew = self.params.get("inventory_skew", 10)  # Coefficient pour ajuster l'offset selon la position

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        orders = []
        default_fair = self.params.get("fair_value", 10000)
        # Calcul du mid price et mise à jour de l'historique externe (dans trader_state)
        mid = self.compute_mid_price(order_depth, default_fair)
        history = self.update_history(trader_state, mid)
        avg = self.rolling_average(history)
        std = self.rolling_std(history, avg)
        
        # Calcul dynamique de l'offset en fonction de la volatilité (écart-type)
        dynamic_offset = self.base_offset + self.volatility_coeff * std
        
        # Calcul de l'inventory skew : si position est positive (long) -> skew pour baisser le prix de vente ; si négative (short), augmenter le prix d'achat.
        if position > 0:
            skew = self.inventory_skew * (position / self.position_limit)
        elif position < 0:
            skew = self.inventory_skew * (abs(position) / self.position_limit)
        else:
            skew = 0

        fair_value = avg if avg > 0 else default_fair
        print(f"[RAINFOREST_RESIN] Mid: {mid}, Moyenne: {avg}, Std: {std}, Offset dynamique: {dynamic_offset}, Skew inventaire: {skew}")
        
        # Détermination des prix de base pour les ordres
        base_buy_price = fair_value - dynamic_offset
        base_sell_price = fair_value + dynamic_offset
        
        # Ajustement selon la position : si position négative, on augmente le prix d'achat ; si positive, on baisse le prix de vente.
        if position < 0:
            bid_price = round(base_buy_price + skew)
        else:
            bid_price = round(base_buy_price)
        if position > 0:
            ask_price = round(base_sell_price - skew)
        else:
            ask_price = round(base_sell_price)
        print(f"[RAINFOREST_RESIN] Prix d'achat (bid): {bid_price}, Prix de vente (ask): {ask_price}")
        
        # Calcul des quantités autorisées
        buy_qty = self.allowed_buy_quantity(position)
        sell_qty = self.allowed_sell_quantity(position)
        
        # Si la position est trop élevée (plus de 80% de la limite), réduire la taille des ordres pour limiter le risque
        if abs(position) > 0.8 * self.position_limit:
            reduction_factor = 0.5
            buy_qty = int(buy_qty * reduction_factor)
            sell_qty = int(sell_qty * reduction_factor)
            print(f"[RAINFOREST_RESIN] Position élevée ({position}). Réduction des ordres: BUY = {buy_qty}, SELL = {sell_qty}")
        
        if buy_qty > 0:
            orders.append(Order(self.product, bid_price, buy_qty))
            print(f"[RAINFOREST_RESIN] Market Making BUY order: {buy_qty} à {bid_price}")
        if sell_qty > 0:
            orders.append(Order(self.product, ask_price, -sell_qty))
            print(f"[RAINFOREST_RESIN] Market Making SELL order: {sell_qty} à {ask_price}")
        
        return orders, trader_state


##############################################
# Stratégie pour KELP (Mean Reversion)
##############################################
class KelpStrategy(ProductStrategy):
    def __init__(self, params: Dict):
        # Prix de base = 2000, position_limit = 50 pour KELP
        super().__init__("KELP", params, position_limit=50)
        # Paramètres supplémentaires pour la stratégie améliorée
        self.bollinger_multiplier = self.params.get("bollinger_multiplier", 1.5)
        self.min_trade_threshold = self.params.get("min_trade_threshold", 0.2)  # Seuil minimal pour déclencher un trade

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        orders = []
        default_fair = self.params.get("fair_value", 2000)
        # Calcul du mid price et mise à jour de l'historique
        mid = self.compute_mid_price(order_depth, default_fair)
        history = self.update_history(trader_state, mid)
        avg = self.rolling_average(history)
        std = self.rolling_std(history, avg)
        
        # Calcul des bandes de Bollinger
        lower_band = avg - self.bollinger_multiplier * std
        upper_band = avg + self.bollinger_multiplier * std
        
        print(f"[KELP] Mid actuel: {mid}, Moyenne: {avg}, Std: {std}")
        print(f"[KELP] Bande inférieure: {lower_band}, Bande supérieure: {upper_band}")
        
        # Initialisation de la quantité à trader (en proportion)
        trade_qty = 0
        signal = 0  # + pour signal d'achat, - pour signal de vente
        
        if mid < lower_band:
            # Distance normalisée par écart-type
            factor = (lower_band - mid) / std if std > 0 else 0
            print(f"[KELP] Signal d'achat potentiel, distance factor: {factor}")
            if factor > self.min_trade_threshold:
                signal = 1  # Achat
                # La taille de l'ordre est proportionnelle au factor, maximum = allowed_buy_quantity
                allowed = self.allowed_buy_quantity(position)
                trade_qty = int(allowed * min(factor, 1))
        elif mid > upper_band:
            factor = (mid - upper_band) / std if std > 0 else 0
            print(f"[KELP] Signal de vente potentiel, distance factor: {factor}")
            if factor > self.min_trade_threshold:
                signal = -1  # Vente
                allowed = self.allowed_sell_quantity(position)
                trade_qty = int(allowed * min(factor, 1))
        
        if signal == 1 and trade_qty > 0:
            # On place un ordre d'achat au niveau du mid (ou on peut utiliser mid arrondi)
            orders.append(Order(self.product, round(mid), trade_qty))
            print(f"[KELP] Signal d'achat confirmé: Ordre BUY de {trade_qty} à {round(mid)}")
        elif signal == -1 and trade_qty > 0:
            orders.append(Order(self.product, round(mid), -trade_qty))
            print(f"[KELP] Signal de vente confirmé: Ordre SELL de {trade_qty} à {round(mid)}")
        else:
            print(f"[KELP] Aucun signal de trading suffisamment fort détecté.")
        
        # Gestion du risque : si l'inventaire est trop élevé (plus de 80% de la limite), réduire la taille des ordres
        if abs(position) > 0.8 * self.position_limit:
            reduction_factor = 0.5
            reduced_orders = []
            for o in orders:
                new_qty = int(abs(o.quantity) * reduction_factor)
                if new_qty > 0:
                    new_qty = new_qty if o.quantity > 0 else -new_qty
                    reduced_orders.append(Order(self.product, o.price, new_qty))
                    print(f"[KELP] Réduction d'ordre: Quantité {o.quantity} réduite à {new_qty}")
            orders = reduced_orders
        
        return orders, trader_state


##############################################
# Stratégie pour SQUID_INK (Trend Following / Momentum)
##############################################
class SquidInkStrategy(ProductStrategy):
    def __init__(self, params: Dict):
        # Prix de base = 2000, position_limit = 50 pour SQUID_INK
        super().__init__("SQUID_INK", params, position_limit=50)
        # Paramètres spécifiques pour la stratégie, avec des valeurs par défaut :
        self.bollinger_multiplier = self.params.get("bollinger_multiplier", 1.5)
        self.min_trade_threshold = self.params.get("min_trade_threshold", 0.2)

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        orders = []
        default_fair = self.params.get("fair_value", 2000)
        
        # Calcul du mid price et mise à jour de l'historique dans le trader_state
        mid = self.compute_mid_price(order_depth, default_fair)
        history = self.update_history(trader_state, mid)
        avg = self.rolling_average(history)
        std = self.rolling_std(history, avg)
        
        # Calcul des bandes de Bollinger
        lower_band = avg - self.bollinger_multiplier * std
        upper_band = avg + self.bollinger_multiplier * std
        
        print(f"[SQUID_INK] Mid actuel: {mid}, Moyenne: {avg}, Ecart-type: {std}")
        print(f"[SQUID_INK] Bande inférieure: {lower_band}, Bande supérieure: {upper_band}")
        
        trade_qty = 0
        signal = 0  # +1 pour signal d'achat, -1 pour signal de vente
        
        # Signal d'achat : mid inférieur à la bande inférieure
        if mid < lower_band:
            factor = (lower_band - mid) / std if std > 0 else 0
            print(f"[SQUID_INK] Signal d'achat potentiel, distance factor: {factor}")
            if factor > self.min_trade_threshold:
                signal = 1
                allowed = self.allowed_buy_quantity(position)
                trade_qty = int(allowed * min(factor, 1))
        # Signal de vente : mid supérieur à la bande supérieure
        elif mid > upper_band:
            factor = (mid - upper_band) / std if std > 0 else 0
            print(f"[SQUID_INK] Signal de vente potentiel, distance factor: {factor}")
            if factor > self.min_trade_threshold:
                signal = -1
                allowed = self.allowed_sell_quantity(position)
                trade_qty = int(allowed * min(factor, 1))
        
        if signal == 1 and trade_qty > 0:
            orders.append(Order(self.product, round(mid), trade_qty))
            print(f"[SQUID_INK] Signal d'achat confirmé: Ordre BUY de {trade_qty} à {round(mid)}")
        elif signal == -1 and trade_qty > 0:
            orders.append(Order(self.product, round(mid), -trade_qty))
            print(f"[SQUID_INK] Signal de vente confirmé: Ordre SELL de {trade_qty} à {round(mid)}")
        else:
            print(f"[SQUID_INK] Aucune condition de trading suffisamment forte détectée.")
        
        # Gestion du risque : réduction des quantités si la position est trop élevée
        if abs(position) > 0.8 * self.position_limit:
            reduction_factor = 0.5
            reduced_orders = []
            for o in orders:
                new_qty = int(abs(o.quantity) * reduction_factor)
                if new_qty > 0:
                    new_qty = new_qty if o.quantity > 0 else -new_qty
                    reduced_orders.append(Order(self.product, o.price, new_qty))
                    print(f"[SQUID_INK] Réduction d'ordre: quantité {o.quantity} réduite à {new_qty}")
            orders = reduced_orders
        
        return orders, trader_state


##############################################
# Classe Trader principale
##############################################
class Trader:
    def __init__(self, params: Dict = None):
        # Paramètres par défaut pour chaque produit avec les prix de base adaptés
        if params is None:
            params = {
                "KELP": {"fair_value": 2000, "reversion_threshold": 50},
                "RAINFOREST_RESIN": {"fair_value": 10000, "scalping_offset": 1},
                "SQUID_INK": {"fair_value": 2000}
            }
        self.params = params
        # Instanciation des stratégies pour chaque produit (limite de position = 50 pour tous)
        self.strategies = {
            "KELP": KelpStrategy(self.params.get("KELP", {})),
            "RAINFOREST_RESIN": RainforestResinStrategy(self.params.get("RAINFOREST_RESIN", {})),
            "SQUID_INK": SquidInkStrategy(self.params.get("SQUID_INK", {}))
        }

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        print("=== Début de l'exécution du Trader ===")
        
        # Affichage des positions et trades pour chaque produit
        for prod in ["KELP", "RAINFOREST_RESIN", "SQUID_INK"]:
            pos = state.position.get(prod, 0)
            print(f"Position actuelle pour {prod}: {pos}")
            if prod in state.own_trades:
                trades = state.own_trades.get(prod, [])
                profit = compute_profit(trades)
                print(f"Trades récents pour {prod}: {trades}")
                print(f"Profit cumulé (naïf) pour {prod}: {profit}")
            else:
                print(f"Aucun trade récent pour {prod}.")
        
        # Chargement de l'état précédent depuis traderData
        trader_data = {}
        if state.traderData and state.traderData != "":
            trader_data = jsonpickle.decode(state.traderData)
            print("État précédent chargé depuis traderData.")
        else:
            trader_data = {}
            print("Pas d'état précédent détecté. Initialisation de traderData.")

        result = {}
        # Pour chaque produit disposant d'une stratégie et présent dans l'order_depth
        for product, strategy in self.strategies.items():
            if product in state.order_depths:
                print(f"\n--- Traitement du produit: {product} ---")
                prod_state = trader_data.get(product, {})
                orders, updated_state = strategy.run_strategy(
                    state.order_depths[product],
                    state.position.get(product, 0),
                    state.observations,
                    prod_state
                )
                result[product] = orders
                trader_data[product] = updated_state
                print(f"[{product}] Ordres générés: {orders}")

        new_trader_data = jsonpickle.encode(trader_data)
        conversions = 0  # Aucune conversion dans cet exemple
        print("=== Fin de l'exécution du Trader ===\n")
        return result, conversions, new_trader_data
