# app/callbacks/callback.py
# app/callbacks/callback.py
from dash.dependencies import Input, Output
from dash import dcc, html
from controllers import csv_controller, trade_controller, chart_controller

def register_callbacks(app):

    @ app.callback(
        [Output('sma-period-container', 'style'),
        Output('ema-period-container', 'style')],
        [Input('tech-indicators-checklist', 'value')]
    )
    def update_period_fields(selected_indicators):
        sma_style = {'display': 'block', 'marginTop': '10px'} if 'sma' in selected_indicators else {'display': 'none'}
        ema_style = {'display': 'block', 'marginTop': '10px'} if 'ema' in selected_indicators else {'display': 'none'}
        return sma_style, ema_style

    @app.callback(
        Output('price-options', 'style'),
        [Input('tabs-graph', 'value')]
    )
    def update_price_options_visibility(tab_value):
        if tab_value == 'tab-price':
            return {'textAlign': 'center', 'padding': '10px 0', 'display': 'block'}
        else:
            return {'display': 'none'}

    @app.callback(
        [Output('start-timestamp-dropdown', 'options'),
         Output('end-timestamp-dropdown', 'options')],
        [Input('product-dropdown', 'value'),
         Input('day-dropdown', 'value')]
    )
    def update_timestamp_options(product, day):
        data = csv_controller.load_market_data(product, day)
        if data.empty or 'timestamp' not in data.columns:
            return [], []
        data['timestamp'] = data['timestamp'].apply(lambda x: float(x) if x is not None else None)
        unique_ts = sorted(data['timestamp'].dropna().unique())
        options = [{'label': str(ts), 'value': ts} for ts in unique_ts]
        return options, options

    @ app.callback(
        Output('tabs-content', 'children'),
        [Input('tabs-graph', 'value'),
        Input('product-dropdown', 'value'),
        Input('day-dropdown', 'value'),
        Input('start-timestamp-dropdown', 'value'),
        Input('end-timestamp-dropdown', 'value'),
        Input('price-options-dropdown', 'value')]
    )

    def render_content(tab, product, day, start_ts, end_ts, price_options):
        # Chargement des données
        market_data = csv_controller.load_market_data(product, day)
        trades_data = trade_controller.load_trades_data(product, day)
        
        # Pour l'onglet Price/Spread, appliquer un filtrage par timestamp
        if not market_data.empty and start_ts is not None and end_ts is not None:
            market_data = market_data[(market_data['timestamp'] >= start_ts) & (market_data['timestamp'] <= end_ts)]
        if not trades_data.empty and start_ts is not None and end_ts is not None:
            trades_data = trades_data[(trades_data['timestamp'] >= start_ts) & (trades_data['timestamp'] <= end_ts)]
        
        if tab == 'tab-price':
            fig = chart_controller.create_price_chart(market_data, price_options, trades_data)
        elif tab == 'tab-volume':
            fig = chart_controller.create_volume_chart(market_data)
        elif tab == 'tab-trades':
            fig = chart_controller.create_trades_chart(trades_data)
        elif tab == 'tab-pnl':
            fig = chart_controller.create_pnl_chart(market_data)
        elif tab == 'tab-orderbook':
            if start_ts is None:
                from plotly.graph_objs import go
                fig = go.Figure(layout=go.Layout(title="Sélectionnez un timestamp pour afficher le carnet d'ordres"))
                return dcc.Graph(figure=fig)
            else:
                # Charger les données complètes pour le jour
                full_data = csv_controller.load_market_data(product, day)
                # Extraire les timestamps uniques disponibles
                unique_ts = sorted(full_data['timestamp'].dropna().unique())
                try:
                    idx = unique_ts.index(start_ts)
                except ValueError:
                    idx = 0

                # Construire la liste de trois timestamps : précédent, sélectionné, suivant
                ts_list = []
                if idx - 1 >= 0:
                    ts_list.append(unique_ts[idx - 1])
                ts_list.append(start_ts)
                if idx + 1 < len(unique_ts):
                    ts_list.append(unique_ts[idx + 1])

                # Calculer l'échelle X commune à partir des snapshots affichées
                all_prices = []
                for ts in ts_list:
                    snapshot_df = full_data[full_data['timestamp'] == ts]
                    if snapshot_df.empty:
                        continue
                    snapshot = snapshot_df.iloc[0]
                    for col in snapshot.index:
                        if col.startswith('bid_price_') or col.startswith('ask_price_'):
                            try:
                                price = float(snapshot[col])
                                all_prices.append(price)
                            except (ValueError, TypeError):
                                pass
                    try:
                        all_prices.append(float(snapshot['mid_price']))
                    except (ValueError, TypeError):
                        pass

                if all_prices:
                    min_price = min(all_prices)
                    max_price = max(all_prices)
                    diff = max_price - min_price
                    margin = diff / 2.0 if diff else 0
                    xaxis_range = [min_price - margin, max_price + margin]
                else:
                    xaxis_range = None

                # Préparer les snapshots de trades pour chaque timestamp (s'ils existent)
                trade_snapshots_dict = {}
                for ts in ts_list:
                    ts_trade = trades_data[trades_data['timestamp'] == ts] if not trades_data.empty else None
                    if ts_trade is not None and not ts_trade.empty:
                        trade_snapshots_dict[ts] = ts_trade

                # Créer un graphique pour chaque timestamp en utilisant l'échelle X commune
                graphs = []
                for ts in ts_list:
                    trade_snapshot = trade_snapshots_dict.get(ts, None)
                    fig = chart_controller.create_orderbook_chart(full_data, ts, trade_snapshot, xaxis_range)
                    graphs.append(dcc.Graph(figure=fig))

                # Affichage vertical des trois graphiques
                return html.Div(graphs, style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center'
                })
        else:
            fig = chart_controller.create_price_chart(market_data, price_options, trades_data)
        
        return dcc.Graph(figure=fig)