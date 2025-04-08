# app/controllers/trade_controller.py
import pandas as pd
import os

TRADE_DIR = os.path.join(os.path.dirname(__file__), '../../web_app/data/trades')

def get_trades_filename(day):
    if day < 0:
        return f"trades_round_1_day_minus{abs(day)}.csv"
    elif day == 0:
        return "trades_round_1_day_0.csv"
    else:
        return f"trades_round_1_day_{day}.csv"

def load_trades_data(product, day):
    filename = get_trades_filename(day)
    filepath = os.path.join(TRADE_DIR, filename)
    try:
        df = pd.read_csv(filepath, sep=';')
        # Filtrer sur le produit souhaité dans la colonne "symbol"
        df_product = df[df['symbol'] == product]
        return df_product
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {filepath}: {e}")
        return pd.DataFrame()
