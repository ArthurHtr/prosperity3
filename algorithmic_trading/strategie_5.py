from datamodel import OrderDepth, TradingState, Order, Trade
from typing import List, Dict, Tuple
import jsonpickle
import math

##############################################
# Classe de base pour la stratégie par produit
##############################################
class ProductStrategy:
    def __init__(self, product: str, params: Dict, position_limit: int):
        self.product = product
        self.params = params
        self.position_limit = position_limit  # Ici, 50 pour tous
        # L'état interne est prévu pour stocker, par exemple, l'historique des mid prices.
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
        Logique par défaut : on applique la méthode basique.
        Les stratégies dérivées surchargeront cette méthode.
        """
        orders = []
        default_fair = self.params.get("fair_value", 100)
        fair_value = self.compute_mid_price(order_depth, default_fair)
        orders.extend(self.basic_orders(fair_value, order_depth, position))
        return orders, trader_state

    def basic_orders(self, fair_value: float, order_depth: OrderDepth, position: int) -> List[Order]:
        """
        Logique simple : si le meilleur ask est inférieur à fair_value, on passe un ordre d'achat ;
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
# Stratégie pour RAINFOREST_RESIN (Market Making / Scalping amélioré)
##############################################
class RainforestResinStrategy(ProductStrategy):
    def __init__(self, params: Dict):
        # Prix de base = 10000, position_limit = 50 pour RAINFOREST_RESIN
        super().__init__("RAINFOREST_RESIN", params, position_limit=50)
        self.base_offset = self.params.get("scalping_offset", 1)
        self.volatility_coeff = self.params.get("volatility_coeff", 0.1)
        self.inventory_skew = self.params.get("inventory_skew", 10)
        self.imbalance_coeff = self.params.get("imbalance_coeff", 0.5)

    def compute_orderbook_imbalance(self, order_depth: OrderDepth) -> float:
        # Calcule l'imbalance : (volume acheteur - volume vendeur) / volume total
        buy_vol = sum(order_depth.buy_orders.values()) if order_depth.buy_orders else 0
        sell_vol = sum(abs(v) for v in order_depth.sell_orders.values()) if order_depth.sell_orders else 0
        total = buy_vol + sell_vol
        if total > 0:
            imbalance = (buy_vol - sell_vol) / total
            print(f"[{self.product}] Imbalance calculé: {imbalance}")
            return imbalance
        return 0.0

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        orders = []
        default_fair = self.params.get("fair_value", 10000)
        mid = self.compute_mid_price(order_depth, default_fair)
        history = self.update_history(trader_state, mid)
        avg = self.rolling_average(history)
        std = self.rolling_std(history, avg)
        
        dynamic_offset = self.base_offset + self.volatility_coeff * std
        imbalance = self.compute_orderbook_imbalance(order_depth)
        dynamic_offset += self.imbalance_coeff * imbalance * std
        
        if position > 0:
            skew = self.inventory_skew * (position / self.position_limit)
        elif position < 0:
            skew = self.inventory_skew * (abs(position) / self.position_limit)
        else:
            skew = 0

        fair_value = avg if avg > 0 else default_fair
        print(f"[RAINFOREST_RESIN] Mid: {mid}, Moyenne: {avg}, Std: {std}, Offset dynamique: {dynamic_offset}, Skew: {skew}")

        base_buy_price = fair_value - dynamic_offset
        base_sell_price = fair_value + dynamic_offset
        if position < 0:
            bid_price = round(base_buy_price + skew)
        else:
            bid_price = round(base_buy_price)
        if position > 0:
            ask_price = round(base_sell_price - skew)
        else:
            ask_price = round(base_sell_price)
        print(f"[RAINFOREST_RESIN] Prix d'achat (bid): {bid_price}, Prix de vente (ask): {ask_price}")

        buy_qty = self.allowed_buy_quantity(position)
        sell_qty = self.allowed_sell_quantity(position)
        if abs(position) > 0.8 * self.position_limit:
            reduction_factor = 0.5
            buy_qty = int(buy_qty * reduction_factor)
            sell_qty = int(sell_qty * reduction_factor)
            print(f"[RAINFOREST_RESIN] Position élevée ({position}). Réduction des quantités: BUY={buy_qty}, SELL={sell_qty}")

        if buy_qty > 0:
            orders.append(Order(self.product, bid_price, buy_qty))
            print(f"[RAINFOREST_RESIN] ORDRE BUY: {buy_qty} à {bid_price}")
        if sell_qty > 0:
            orders.append(Order(self.product, ask_price, -sell_qty))
            print(f"[RAINFOREST_RESIN] ORDRE SELL: {sell_qty} à {ask_price}")

        return orders, trader_state

##############################################
# Stratégie pour KELP (Mean Reversion améliorée avec Bollinger Bands et filtre RSI)
##############################################
class KelpStrategy(ProductStrategy):
    def __init__(self, params: Dict):
        # Prix de base = 2000, position_limit = 50 pour KELP
        super().__init__("KELP", params, position_limit=50)
        self.bollinger_multiplier = self.params.get("bollinger_multiplier", 1.5)
        self.min_trade_threshold = self.params.get("min_trade_threshold", 0.2)
        self.rsi_period = self.params.get("rsi_period", 14)
        self.rsi_oversold = self.params.get("rsi_oversold", 30)
        self.rsi_overbought = self.params.get("rsi_overbought", 70)

    def compute_rsi(self, history: List[float]) -> float:
        if len(history) < self.rsi_period + 1:
            return 50  # Valeur neutre
        gains = []
        losses = []
        for i in range(-self.rsi_period, 0):
            change = history[i] - history[i - 1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
        avg_gain = sum(gains) / self.rsi_period if gains else 0
        avg_loss = sum(losses) / self.rsi_period if losses else 0
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        print(f"[KELP] RSI calculé: {rsi}")
        return rsi

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        orders = []
        default_fair = self.params.get("fair_value", 2000)
        mid = self.compute_mid_price(order_depth, default_fair)
        history = self.update_history(trader_state, mid)
        avg = self.rolling_average(history)
        std = self.rolling_std(history, avg)
        lower_band = avg - self.bollinger_multiplier * std
        upper_band = avg + self.bollinger_multiplier * std
        print(f"[KELP] Mid: {mid}, Moyenne: {avg}, Std: {std}, Lower band: {lower_band}, Upper band: {upper_band}")
        rsi = self.compute_rsi(history)
        print(f"[KELP] RSI: {rsi}")
        trade_qty = 0
        signal = 0  # 1 pour achat, -1 pour vente
        if mid < lower_band and rsi < self.rsi_oversold:
            factor = (lower_band - mid) / (std if std > 0 else 1)
            print(f"[KELP] Signal d'achat potentiel, factor: {factor}")
            if factor > self.min_trade_threshold:
                signal = 1
                allowed = self.allowed_buy_quantity(position)
                trade_qty = int(allowed * min(factor, 1))
        elif mid > upper_band and rsi > self.rsi_overbought:
            factor = (mid - upper_band) / (std if std > 0 else 1)
            print(f"[KELP] Signal de vente potentiel, factor: {factor}")
            if factor > self.min_trade_threshold:
                signal = -1
                allowed = self.allowed_sell_quantity(position)
                trade_qty = int(allowed * min(factor, 1))
        if signal == 1 and trade_qty > 0:
            orders.append(Order(self.product, round(mid), trade_qty))
            print(f"[KELP] ORDRE BUY généré: {trade_qty} à {round(mid)}")
        elif signal == -1 and trade_qty > 0:
            orders.append(Order(self.product, round(mid), -trade_qty))
            print(f"[KELP] ORDRE SELL généré: {trade_qty} à {round(mid)}")
        else:
            print(f"[KELP] Aucun signal fort détecté.")
        if abs(position) > 0.8 * self.position_limit:
            reduction_factor = 0.5
            reduced_orders = []
            for o in orders:
                new_qty = int(abs(o.quantity) * reduction_factor)
                if new_qty > 0:
                    new_qty = new_qty if o.quantity > 0 else -new_qty
                    reduced_orders.append(Order(self.product, o.price, new_qty))
                    print(f"[KELP] Réduction d'ordre: {o.quantity} réduit à {new_qty}")
            orders = reduced_orders
        return orders, trader_state

##############################################
# Stratégie pour SQUID_INK (Trend Following / Momentum amélioré)
##############################################
class SquidInkStrategy(ProductStrategy):
    def __init__(self, params: Dict):
        # Prix de base = 2000, position_limit = 50 pour SQUID_INK
        super().__init__("SQUID_INK", params, position_limit=50)
        self.momentum_window = self.params.get("momentum_window", 5)
        self.momentum_threshold = self.params.get("momentum_threshold", 0.5)

    def compute_momentum(self, history: List[float]) -> float:
        n = self.momentum_window
        if len(history) < n:
            return 0
        x_vals = list(range(n))
        y_vals = history[-n:]
        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
        den = sum((x - mean_x) ** 2 for x in x_vals)
        slope = num / den if den != 0 else 0
        print(f"[SQUID_INK] Momentum (pente) calculé sur {n} points: {slope}")
        return slope

    def run_strategy(self, order_depth: OrderDepth, position: int, observation, trader_state: Dict) -> (List[Order], Dict):
        orders = []
        default_fair = self.params.get("fair_value", 2000)
        mid = self.compute_mid_price(order_depth, default_fair)
        history = self.update_history(trader_state, mid)
        momentum = self.compute_momentum(history)
        if abs(momentum) < self.momentum_threshold:
            print(f"[SQUID_INK] Momentum trop faible ({momentum}). Aucun trade.")
            return orders, trader_state
        print(f"[SQUID_INK] Mid: {mid}, Momentum: {momentum}")
        if momentum > 0:
            allowed = self.allowed_buy_quantity(position)
            trade_qty = allowed
            orders.append(Order(self.product, round(mid), trade_qty))
            print(f"[SQUID_INK] Signal momentum positif: ORDRE BUY de {trade_qty} à {round(mid)}")
        elif momentum < 0:
            allowed = self.allowed_sell_quantity(position)
            trade_qty = allowed
            orders.append(Order(self.product, round(mid), -trade_qty))
            print(f"[SQUID_INK] Signal momentum négatif: ORDRE SELL de {trade_qty} à {round(mid)}")
        if abs(position) > 0.8 * self.position_limit:
            reduction_factor = 0.5
            new_orders = []
            for o in orders:
                new_qty = int(abs(o.quantity) * reduction_factor)
                if new_qty > 0:
                    new_qty = new_qty if o.quantity > 0 else -new_qty
                    new_orders.append(Order(self.product, o.price, new_qty))
                    print(f"[SQUID_INK] Réduction d'ordre: {o.quantity} réduit à {new_qty}")
            orders = new_orders
        return orders, trader_state

##############################################
# Classe Trader principale
##############################################
class Trader:
    def __init__(self, params: Dict = None):
        if params is None:
            params = {
                "KELP": {"fair_value": 2000, "reversion_threshold": 50, "bollinger_multiplier": 1.5, 
                         "min_trade_threshold": 0.2, "rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70},
                "RAINFOREST_RESIN": {"fair_value": 10000, "scalping_offset": 1, "volatility_coeff": 0.1, 
                                      "inventory_skew": 10, "imbalance_coeff": 0.5},
                "SQUID_INK": {"fair_value": 2000, "momentum_window": 5, "momentum_threshold": 0.5}
            }
        self.params = params
        self.strategies = {
            "KELP": KelpStrategy(self.params.get("KELP", {})),
            "RAINFOREST_RESIN": RainforestResinStrategy(self.params.get("RAINFOREST_RESIN", {})),
            "SQUID_INK": SquidInkStrategy(self.params.get("SQUID_INK", {}))
        }

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        print("=== Début de l'exécution du Trader ===")
        
        # Affichage des positions pour chaque produit
        for prod in ["KELP", "RAINFOREST_RESIN", "SQUID_INK"]:
            pos = state.position.get(prod, 0)
            print(f"Position actuelle pour {prod}: {pos}")
            if prod in state.own_trades:
                print(f"Trades récents pour {prod}: {state.own_trades.get(prod)}")
            else:
                print(f"Aucun trade récent pour {prod}.")
        
        # Chargement de l'état précédent depuis traderData
        if state.traderData and state.traderData != "":
            trader_data = jsonpickle.decode(state.traderData)
            print("État précédent chargé depuis traderData.")
        else:
            trader_data = {}
            print("Pas d'état précédent détecté. Initialisation de traderData.")
        
        result = {}
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

