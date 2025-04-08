"""
main.py
Point d'entrée de l'algo de trading.
Ce fichier instancie le Trader et distribue l'état aux stratégies spécifiques à chaque produit.
"""

import json
from models.datamodel import TradingState, Order
from trader_base import Trader

def main():
    # Simulation : Créez ou chargez l'objet TradingState selon vos tests / environnement live.
    # state = ... 
    # Exemple simplifié:
    state = TradingState(
        traderData="",
        timestamp=1000,
        listings={},  # Remplir avec les listings
        order_depths={},  # Remplir avec les OrderDepth par produit
        own_trades={},
        market_trades={},
        position={},
        observations={}
    )

    trader = Trader()
    result, conversions, traderData = trader.run(state)
    print("Ordres envoyés :", result)
    print("Conversions :", conversions)
    print("Trader Data :", traderData)

if __name__ == "__main__":
    main()