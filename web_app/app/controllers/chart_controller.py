# app/controllers/chart_controller.py
# app/controllers/chart_controller.py
import plotly.graph_objs as go

def create_price_chart(data, display_options=[], trades_data=None):
    """
    Crée un graphique des prix avec la possibilité de sélectionner via un menu déroulant
    les données à afficher.
    
    Paramètres :
      - data: DataFrame contenant les données de marché.
      - display_options: liste de chaînes correspondant aux colonnes à afficher.
        Les options possibles sont par exemple :
           'mid_price', 'bid_price_1', 'bid_price_2', 'bid_price_3',
           'ask_price_1', 'ask_price_2', 'ask_price_3',
           et 'overlay_trades' pour activer l'overlay des trades.
      - trades_data: DataFrame des trades à superposer si 'overlay_trades' est dans display_options.
    """
    if data.empty:
        return go.Figure(data=[], layout=go.Layout(title="Aucune donnée pour le graphique de prix"))
    
    fig = go.Figure()
    
    # Pour chaque option cochée (sauf overlay_trades), on ajoute une trace si la colonne existe
    for option in display_options:
        if option == 'overlay_trades':
            continue
        if option in data.columns:
            mode = 'lines+markers' if option == 'mid_price' else 'lines'
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data[option],
                mode=mode,
                name=option.replace('_', ' ').title()
            ))
    
    # Si l'overlay des trades est demandé
    if 'overlay_trades' in display_options and trades_data is not None and not trades_data.empty:
        fig.add_trace(go.Scatter(
            x=trades_data['timestamp'],
            y=trades_data['price'],
            mode='markers',
            marker=dict(size=10, color='rgba(255,0,0,0.7)'),
            name='Trades'
        ))
    
    fig.update_layout(
        title="Graphique des Prix et Spread",
        xaxis_title="Timestamp",
        yaxis_title="Prix",
        autosize=True,
        margin={'l':50, 'r':20, 't':50, 'b':50},
        xaxis=dict(autorange=True),
        yaxis=dict(autorange=True)
    )
    return fig


def create_volume_chart(data):
    if data.empty:
        return go.Figure(data=[], layout=go.Layout(title="Aucune donnée pour le graphique de volumes"))
    fig = go.Figure()
    # Graphique à barres pour les volumes bid et ask
    fig.add_trace(go.Bar(x=data['timestamp'], y=data['bid_volume_1'], name='Bid Volume 1'))
    fig.add_trace(go.Bar(x=data['timestamp'], y=data['bid_volume_2'], name='Bid Volume 2'))
    fig.add_trace(go.Bar(x=data['timestamp'], y=data['bid_volume_3'], name='Bid Volume 3'))
    fig.add_trace(go.Bar(x=data['timestamp'], y=data['ask_volume_1'], name='Ask Volume 1'))
    fig.add_trace(go.Bar(x=data['timestamp'], y=data['ask_volume_2'], name='Ask Volume 2'))
    fig.add_trace(go.Bar(x=data['timestamp'], y=data['ask_volume_3'], name='Ask Volume 3'))
    fig.update_layout(
        title="Graphique des Volumes",
        xaxis_title="Timestamp",
        yaxis_title="Volume",
        barmode='group',
        autosize=True,
        margin={'l':50, 'r':20, 't':50, 'b':50}
    )
    return fig

def create_trades_chart(trades_data):
    if trades_data.empty:
        return go.Figure(data=[], layout=go.Layout(title="Aucune donnée pour le graphique des trades"))
    
    # Calcul de la taille des marqueurs : scale quantity par 3 et imposer une taille minimale
    marker_sizes = trades_data['quantity'] * 3
    marker_sizes = marker_sizes.apply(lambda x: x if x > 6 else 6)
    
    # Création d'un texte de survol pour chaque trade (affiche le prix et la quantité)
    hover_text = trades_data.apply(lambda row: f"Price: {row['price']}<br>Quantity: {row['quantity']}", axis=1)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trades_data['timestamp'],
        y=trades_data['price'],
        mode='markers',
        marker=dict(
            size=marker_sizes,
            color='red',
            opacity=0.8,
            line=dict(width=1, color='black')
        ),
        text=hover_text,
        hoverinfo='text',
        name='Trades'
    ))
    fig.update_layout(
        title="Graphique des Trades",
        xaxis_title="Timestamp",
        yaxis_title="Prix",
        autosize=True,
        margin={'l':50, 'r':20, 't':50, 'b':50},
        hovermode='closest'
    )
    return fig

def create_pnl_chart(data):
    if data.empty:
        return go.Figure(data=[], layout=go.Layout(title="Aucune donnée pour le graphique P&L"))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['timestamp'], y=data['profit_and_loss'],
        mode='lines+markers', name='P&L'
    ))
    fig.update_layout(
        title="Graphique du Profit & Loss",
        xaxis_title="Timestamp",
        yaxis_title="P&L",
        autosize=True,
        margin={'l':50, 'r':20, 't':50, 'b':50}
    )
    return fig




def create_orderbook_chart(data, selected_timestamp, trade_snapshot=None, xaxis_range=None):
    """
    Crée un graphique du carnet d'ordres pour un timestamp précis.
    - Axe X : Prix.
    - Axe Y : Volume.
    - Extraction dynamique des niveaux (bid et ask) pour le snapshot sélectionné.
    - Trace une ligne verticale indiquant le mid price.
    - Si trade_snapshot est fourni, ajoute un marker (taille fixe) indiquant les trades.
    - Applique l'échelle X (xaxis_range) calculée à partir des snapshots affichées.
    """
    # Filtrer pour obtenir la snapshot correspondant au timestamp sélectionné
    snapshot_df = data[data['timestamp'] == selected_timestamp]
    if snapshot_df.empty:
        return go.Figure(data=[], layout=go.Layout(title=f"Aucune donnée pour le timestamp {selected_timestamp}"))
    snapshot = snapshot_df.iloc[0]

    try:
        mid_price = float(snapshot['mid_price'])
    except (ValueError, TypeError):
        mid_price = None

    # Extraction dynamique des niveaux de bids
    bid_levels = []
    for col in snapshot.index:
        if col.startswith("bid_price_"):
            try:
                price = float(snapshot[col])
            except (ValueError, TypeError):
                continue
            vol_col = f"bid_volume_{col.split('_')[-1]}"
            try:
                volume = float(snapshot[vol_col]) if vol_col in snapshot.index else 0
            except (ValueError, TypeError):
                volume = 0
            bid_levels.append((price, volume))
    bid_levels.sort(key=lambda x: x[0])

    # Extraction dynamique des niveaux d'asks
    ask_levels = []
    for col in snapshot.index:
        if col.startswith("ask_price_"):
            try:
                price = float(snapshot[col])
            except (ValueError, TypeError):
                continue
            vol_col = f"ask_volume_{col.split('_')[-1]}"
            try:
                volume = float(snapshot[vol_col]) if vol_col in snapshot.index else 0
            except (ValueError, TypeError):
                volume = 0
            ask_levels.append((price, volume))
    ask_levels.sort(key=lambda x: x[0])

    # Créer les traces pour les bids et asks
    bid_trace = go.Bar(
        x=[price for price, _ in bid_levels],
        y=[volume for _, volume in bid_levels],
        name='Bids',
        marker_color='green',
        width=0.5
    )
    ask_trace = go.Bar(
        x=[price for price, _ in ask_levels],
        y=[volume for _, volume in ask_levels],
        name='Asks',
        marker_color='red',
        width=0.5
    )
    traces = [bid_trace, ask_trace]

    # Ajouter la ligne verticale pour le mid price
    if mid_price is not None:
        # Déterminer la hauteur maximale parmi les volumes pour tracer la ligne
        all_volumes = [vol for _, vol in bid_levels + ask_levels]
        max_volume = max(all_volumes) if all_volumes else 0
        traces.append(go.Scatter(
            x=[mid_price, mid_price],
            y=[0, max_volume],
            mode='lines',
            line=dict(color='blue', dash='dash'),
            name='Mid Price'
        ))

    # Ajouter un marqueur pour les trades si disponibles (taille fixe)
    if trade_snapshot is not None and not trade_snapshot.empty:
        traces.append(go.Scatter(
            x=trade_snapshot['price'],
            y=[10] * len(trade_snapshot),  # valeur fixe pour la visibilité
            mode='markers',
            marker=dict(size=10, color='purple'),
            name='Trades'
        ))

    layout = {
        'title': f"Carnet d'ordres au timestamp {selected_timestamp}",
        'xaxis_title': "Prix",
        'yaxis_title': "Volume",
        'autosize': True,
        'margin': {'l':50, 'r':50, 't':50, 'b':50}
    }
    if xaxis_range:
        layout['xaxis'] = {'range': xaxis_range}
    else:
        layout['xaxis'] = {'autorange': True}

    fig = go.Figure(data=traces, layout=layout)
    return fig