web_app/
├── app/
│   ├── __init__.py           # Initialisation de l’application Dash (ou Flask/Dash)
│   ├── app.py                # Point d’entrée pour lancer l’application
│   ├── controllers/
│   │   ├── csv_controller.py     # Chargement et parsing des fichiers CSV de marché
│   │   ├── trade_controller.py   # Chargement et parsing des fichiers CSV de trades
│   │   └── chart_controller.py   # Préparation des données pour les graphiques interactifs
│   ├── models/
│   │   ├── product.py         # Modèle de données pour les produits (SQUID_INK, RAINFOREST_RESIN, etc.)
│   │   ├── trade.py           # Modèle de données pour les trades
│   │   └── simulation.py      # Gestion des données temporelles pour la simulation (day -1, day 0, day 1…)
│   ├── layouts/
│   │   └── layout.py          # Définition du layout de l’application Dash (tableau de bord, sélecteurs, etc.)
│   ├── callbacks/
│   │   └── callbacks.py       # Callbacks Dash pour mettre à jour dynamiquement les graphiques et contrôler la simulation
│   └── assets/
│       └── styles.css         # Fichier CSS pour styliser l’interface
├── data/
│   ├── csv/
│   │   ├── day_minus1.csv     # Fichiers CSV contenant les données de marché
│   │   ├── day0.csv
│   │   └── day1.csv
│   └── trades/
│       ├── trades_day0.csv    # Fichiers CSV contenant les données des trades
│       └── trades_day1.csv
├── docs/
│   └── architecture.md        # Documentation de l’architecture du projet et choix techniques