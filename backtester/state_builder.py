# state_builder.py
import pandas as pd
from models.datamodel import TradingState, OrderDepth, Listing, Observation, Trade
from controllers.csv_controller import load_market_data
from controllers.trade_controller import load_trades_data

def build_market_snapshots(product: str, day: int):
    """
    Charge les données de marché via load_market_data() pour le produit et la journée donnée,
    puis crée une liste d'objets TradingState, un snapshot par timestamp.
    """
    df = load_market_data(product, day)
    if df.empty:
        print("Aucune donnée de marché trouvée pour ce produit/jour")
        return []
    
    snapshots = []
    # Groupement par timestamp (les timestamps doivent être numériques ou convertibles en int)
    grouped = df.groupby("timestamp")
    
    for timestamp, group in grouped:
        # On utilise la première ligne de chaque groupe pour créer le Listing
        first_row = group.iloc[0]
        listings = {product: Listing(symbol=product, product=product, denomination="SEASHELLS")}
        
        # Création d'un OrderDepth à partir des informations du snapshot
        od = OrderDepth()
        for i in range(1, 4):
            bid_price = first_row.get(f"bid_price_{i}")
            bid_volume = first_row.get(f"bid_volume_{i}")
            if pd.notna(bid_price) and pd.notna(bid_volume):
                try:
                    price = int(bid_price)
                    volume = int(bid_volume)
                    if volume != 0:
                        od.buy_orders[price] = volume
                except Exception:
                    continue
        for i in range(1, 4):
            ask_price = first_row.get(f"ask_price_{i}")
            ask_volume = first_row.get(f"ask_volume_{i}")
            if pd.notna(ask_price) and pd.notna(ask_volume):
                try:
                    price = int(ask_price)
                    volume = int(ask_volume)
                    if volume != 0:
                        od.sell_orders[price] = -volume
                except Exception:
                    continue
        
        order_depths = {product: od}
        # Initialisation des positions et des historiques de trades
        positions = {product: 0}
        own_trades = {product: []}
        market_trades = {product: []}
        observations = Observation(plainValueObservations={}, conversionObservations={})
        
        ts = TradingState(
            traderData="",
            timestamp=int(timestamp),
            listings=listings,
            order_depths=order_depths,
            own_trades=own_trades,
            market_trades=market_trades,
            position=positions,
            observations=observations
        )
        snapshots.append(ts)
    
    snapshots.sort(key=lambda ts: ts.timestamp)
    return snapshots

def merge_trade_history_into_snapshots(product: str, day: int, snapshots: list):
    """
    Charge les trades historiques via load_trades_data() pour le produit et la journée donnée,
    et les assigne aux objets TradingState correspondants (en se basant sur le timestamp).
    """
    df_trades = load_trades_data(product, day)
    if df_trades.empty:
        print("Aucune donnée de trades trouvée pour ce produit/jour")
        return

    for idx, row in df_trades.iterrows():
        try:
            ts_trade = int(row["timestamp"])
            price = float(row["price"])
            quantity = int(str(row["quantity"]).replace(',', ''))
        except Exception:
            continue
        
        buyer = row.get("buyer", "")
        seller = row.get("seller", "")
        trade = Trade(symbol=product, price=int(price), quantity=quantity, buyer=buyer, seller=seller, timestamp=ts_trade)
        
        # On cherche le TradingState dont le timestamp correspond exactement au trade
        for state in snapshots:
            if state.timestamp == ts_trade:
                if product in state.market_trades:
                    state.market_trades[product].append(trade)
                else:
                    state.market_trades[product] = [trade]
                break  # On suppose qu'un trade n'appartient qu'à un seul snapshot

def build_complete_trading_states(product: str, day: int):
    """
    Combine la création des snapshots de marché et l'attribution des trades historiques.
    Retourne la liste complète des objets TradingState pour le produit et le jour donnés.
    """
    snapshots = build_market_snapshots(product, day)
    merge_trade_history_into_snapshots(product, day, snapshots)
    return snapshots