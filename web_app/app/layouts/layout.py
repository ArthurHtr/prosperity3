# app/layouts/layout.py
from dash import html, dcc

def get_layout():
    return html.Div([
        # Panneau de sélection commun en haut
        html.Div([
            html.Div([
                html.Label("Produit:"),
                dcc.Dropdown(
                    id='product-dropdown',
                    options=[
                        {'label': 'SQUID_INK', 'value': 'SQUID_INK'},
                        {'label': 'RAINFOREST_RESIN', 'value': 'RAINFOREST_RESIN'},
                        {'label': 'KELP', 'value': 'KELP'}
                    ],
                    value='SQUID_INK',
                    style={'width': '200px'}
                )
            ], style={'display': 'inline-block', 'marginRight': '20px'}),
            html.Div([
                html.Label("Jour:"),
                dcc.Dropdown(
                    id='day-dropdown',
                    options=[
                        {'label': 'Day -2', 'value': -2},
                        {'label': 'Day -1', 'value': -1},
                        {'label': 'Day 0',  'value': 0},
                        {'label': 'Day 1',  'value': 1},
                        {'label': 'Day 2',  'value': 2}
                    ],
                    value=0,
                    style={'width': '200px'}
                )
            ], style={'display': 'inline-block', 'marginRight': '20px'}),
            html.Div([
                html.Label("Timestamp de début:"),
                dcc.Dropdown(
                    id='start-timestamp-dropdown',
                    placeholder="Sélectionnez le timestamp de début",
                    style={'width': '200px'}
                )
            ], style={'display': 'inline-block', 'marginRight': '20px'}),
            html.Div([
                html.Label("Timestamp de fin:"),
                dcc.Dropdown(
                    id='end-timestamp-dropdown',
                    placeholder="Sélectionnez le timestamp de fin",
                    style={'width': '200px'}
                )
            ], style={'display': 'inline-block'})
        ], style={'textAlign': 'center', 'padding': '20px 0', 'backgroundColor': '#f4f4f4'}),
        
        # Options spécifiques à l'onglet Prix/Spread (affichées uniquement si l'onglet est actif)
        html.Div([
            html.Label("Sélectionnez les données à afficher:"),
            dcc.Dropdown(
                id='price-options-dropdown',
                options=[
                    {'label': 'Mid Price', 'value': 'mid_price'},
                    {'label': 'Bid Price 1', 'value': 'bid_price_1'},
                    {'label': 'Bid Price 2', 'value': 'bid_price_2'},
                    {'label': 'Bid Price 3', 'value': 'bid_price_3'},
                    {'label': 'Ask Price 1', 'value': 'ask_price_1'},
                    {'label': 'Ask Price 2', 'value': 'ask_price_2'},
                    {'label': 'Ask Price 3', 'value': 'ask_price_3'},
                    {'label': 'Overlay Trades', 'value': 'overlay_trades'}
                ],
                multi=True,
                value=['mid_price']  # valeur par défaut
            )
        ], id='price-options', style={'textAlign': 'center', 'padding': '10px 0', 'display': 'none'}),

        html.Div([
            html.Label("Indicateurs techniques:"),
            dcc.Checklist(
                id='tech-indicators-checklist',
                options=[
                    {'label': 'SMA', 'value': 'sma'},
                    {'label': 'EMA', 'value': 'ema'},
                ],
                value=[],
                labelStyle={'display': 'inline-block', 'marginRight': '10px'}
            ),
            html.Div([
                html.Label("Période SMA:"),
                dcc.Input(id='sma-period', type='number', value=20, min=1, step=1)
            ], id='sma-period-container', style={'display': 'none', 'marginTop': '10px'}),
            html.Div([
                html.Label("Période EMA:"),
                dcc.Input(id='ema-period', type='number', value=20, min=1, step=1)
            ], id='ema-period-container', style={'display': 'none', 'marginTop': '10px'})
        ], style={'textAlign': 'center', 'padding': '10px'}),



        # Zone des onglets et graphiques centrée
        html.Div([
            dcc.Tabs(id='tabs-graph', value='tab-price', children=[
                dcc.Tab(label='Prix / Spread', value='tab-price'),
                dcc.Tab(label='Volumes', value='tab-volume'),
                dcc.Tab(label='Trades', value='tab-trades'),
                dcc.Tab(label='P&L', value='tab-pnl'),
                dcc.Tab(label='Order Book', value='tab-orderbook')
            ]),
            html.Div(id='tabs-content', style={'padding': '20px'})
        ], style={'maxWidth': '1200px', 'margin': '0 auto'})
    ])