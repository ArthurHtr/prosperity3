# backtester/backtester.py
from state_builder import build_complete_trading_states
from sample_trader import SimpleTrader
import os
import pandas as pd
import json
from tabulate import tabulate

def save_trading_states(trading_states, file_path):
    """
    Sauvegarde la liste d'objets TradingState dans un fichier JSON.
    """
    states_list = [json.loads(state.toJSON()) for state in trading_states]
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(states_list, f, indent=4)
    print(f"\nTradingStates saved to '{file_path}'.")

def run_backtest(product: str, day: int):
    """
    Fonction de backtest minimal :
      - Charge la série historique d'états de marché pour le produit et le jour donnés.
      - Le premier TradingState sert d'état d'origine.
      - Pour chaque tick, la stratégie du SimpleTrader est exécutée sur l'état courant.
      - L'état suivant est mis à jour avec les modifications (position, own_trades) issues des décisions de l'algo.
      - Un log chronologique de simulation est généré.
    """
    # Charger la série d'états historiques (snapshots) pour le produit et le jour spécifiés
    historical_states = build_complete_trading_states(product, day)
    if not historical_states:
        print("Aucun état historique chargé.")
        return

    # Sauvegarder les états historiques initiaux pour référence
    initial_states_file = os.path.join("backtester", "reports", "initial_trading_states.json")
    save_trading_states(historical_states, initial_states_file)

    # Instanciation de la stratégie (votre trader simple)
    trader = SimpleTrader()

    # Log de simulation : pour chaque tick, on enregistrera l'état et l'action réalisée
    simulation_log = []

    # On considère le premier état historique comme état initial de simulation
    simulated_state = historical_states[0]
    simulation_log.append({
        "timestamp": simulated_state.timestamp,
        "action": "Initial state",
        "position": simulated_state.position.copy(),
        "own_trades": simulated_state.own_trades.copy()
    })

    # Parcourir les états historiques suivants (par ordre chronologique)
    for next_state in historical_states[1:]:
        # Exécuter la stratégie sur l'état courant et récupérer le résultat (ordres à passer)
        result, conversions, traderData = trader.run(simulated_state)
        
        # Appliquer les actions de l'algo à l'état courant.
        # Ici, nous simulons simplement une exécution immédiate : chaque ordre
        # modifie directement la position et ajoute un trade fictif dans own_trades.
        for prod, orders in result.items():
            for order in orders:
                if order.quantity > 0:
                    # Ordre d'achat : position augmente et on ajoute un trade d'achat
                    simulated_state.position[prod] += order.quantity
                    simulated_state.own_trades[prod].append({
                        "price": order.price,
                        "quantity": order.quantity,
                        "side": "BUY",
                        "timestamp": simulated_state.timestamp
                    })
                else:
                    # Ordre de vente : position diminue et on ajoute un trade de vente
                    simulated_state.position[prod] += order.quantity  # quantity est négative
                    simulated_state.own_trades[prod].append({
                        "price": order.price,
                        "quantity": order.quantity,
                        "side": "SELL",
                        "timestamp": simulated_state.timestamp
                    })

        # Enregistrer les résultats du tick courant dans le log
        simulation_log.append({
            "timestamp": simulated_state.timestamp,
            "action": result,
            "position": simulated_state.position.copy(),
            "own_trades": simulated_state.own_trades.copy()
        })
        
        # Mettre à jour l'état suivant avec la position et l'historique cumulés
        for prod in simulated_state.position:
            next_state.position[prod] = simulated_state.position[prod]
            next_state.own_trades[prod] = simulated_state.own_trades[prod].copy()
        
        # Le tick suivant devient l'état simulé courant
        simulated_state = next_state

    # Enregistrer l'état simulé final dans un fichier JSON
    simulated_states_file = os.path.join("backtester", "reports", "simulated_trading_states.json")
    save_trading_states(historical_states, simulated_states_file)

if __name__ == '__main__':
    product = "RAINFOREST_RESIN"  # Exemple : "RAINFOREST_RESIN", "KELP", "SQUID_INK"
    day = 0                      # À adapter selon vos données
    run_backtest(product, day)