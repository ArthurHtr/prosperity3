# app/app.py
from dash import Dash
from layouts.layout import get_layout
from callbacks.callback import register_callbacks

# Création de l'application Dash
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Définition du layout global
app.layout = get_layout()

# Enregistrement des callbacks pour l'interactivité
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
