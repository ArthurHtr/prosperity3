# app/controllers/csv_controller.py
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/csv')

def get_market_filename(day):
    if day < 0:
        return f"prices_round_1_day_minus{abs(day)}.csv"
    elif day == 0:
        return "prices_round_1_day_0.csv"
    else:
        return f"prices_round_1_day_{day}.csv"

def load_market_data(product, day):
    filename = get_market_filename(day)
    filepath = os.path.join(DATA_DIR, filename)
    try:
        df = pd.read_csv(filepath, sep=';')
        # Filtrer sur le produit souhaité
        df_product = df[df['product'] == product]
        return df_product
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {filepath}: {e}")
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur
    
