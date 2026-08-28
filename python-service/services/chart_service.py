"""
Services pour la génération de graphiques
"""
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour la production
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import io
import base64
from models.schemas import (
    TimeSeriesData,
    MultiSeriesData,
    BarChartData,
    GroupedBarData,
    EvolutionData,
    PieChartData,
)


def generate_timeseries_chart(data: TimeSeriesData):
    """Génère un graphique en ligne (time series) au format Plotly JSON"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.labels,
        y=data.values,
        mode='lines+markers',
        name='Évolution',
        line=dict(color='#1A4D3A', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=data.title,
        xaxis_title="Période",
        yaxis_title=data.ylabel,
        template="plotly_white",
        hovermode='x unified',
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return json.loads(graph_json)


def generate_multiseries_chart(data: MultiSeriesData):
    """Génère un graphique multi-séries au format Plotly JSON"""
    fig = go.Figure()
    
    colors = data.colors if data.colors else ['#2563EB', '#16A34A', '#0066CC', '#FF6600', '#9932CC']
    series_items = list(data.series.items())

    use_dual_axis = False
    if data.dual_axis is True:
        use_dual_axis = len(series_items) == 2
    elif data.dual_axis is not False and len(series_items) == 2:
        left_vals = [float(v or 0) for v in series_items[0][1]]
        right_vals = [float(v or 0) for v in series_items[1][1]]
        left_max = max(left_vals) if left_vals else 0
        right_max = max(right_vals) if right_vals else 0
        if left_max > 0 and right_max > 0:
            ratio = max(left_max / right_max, right_max / left_max)
            use_dual_axis = ratio >= 2.5

    for color_idx, (series_name, series_values) in enumerate(series_items):
        yaxis = 'y2' if use_dual_axis and color_idx == 1 else 'y'
        fig.add_trace(go.Scatter(
            x=data.labels,
            y=series_values,
            mode='lines+markers',
            name=series_name,
            yaxis=yaxis,
            line=dict(
                color=colors[color_idx % len(colors)],
                width=2.5,
                dash='dash' if use_dual_axis and color_idx == 1 else 'solid',
            ),
            marker=dict(size=7),
            connectgaps=False,
            hovertemplate=f'<b>%{{x}}</b><br>{series_name}: %{{y:,.1f}} M<extra></extra>',
        ))

    left_title = data.ylabel if not use_dual_axis else (data.ylabel or series_items[0][0])
    layout_kwargs = dict(
        title=data.title,
        xaxis_title=data.xlabel,
        yaxis_title=left_title,
        template="plotly_white",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(tickangle=-25 if len(data.labels or []) > 6 else 0),
        yaxis=dict(rangemode='tozero', separatethousands=True),
    )

    if use_dual_axis:
        layout_kwargs["yaxis2"] = dict(
            title=data.ylabel2 or series_items[1][0],
            overlaying="y",
            side="right",
            showgrid=False,
            rangemode='tozero',
            separatethousands=True,
        )

    fig.update_layout(**layout_kwargs)
    
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return json.loads(graph_json)


def generate_bar_chart(data: BarChartData):
    """Génère un graphique en barres au format Plotly JSON"""
    colors = data.colors if data.colors else ['#1A4D3A'] * len(data.values)
    
    fig = go.Figure(data=[
        go.Bar(
            x=data.labels,
            y=data.values,
            marker_color=colors,
            text=data.values,
            textposition='auto',
            name='Données'
        )
    ])
    
    fig.update_layout(
        title=data.title,
        xaxis_title=data.xlabel,
        yaxis_title=data.ylabel,
        template="plotly_white",
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return json.loads(graph_json)


def generate_grouped_bar_chart(data: GroupedBarData):
    """Génère un graphique en barres groupées (comparaison de plusieurs séries)"""
    default_colors = ['#2563EB', '#16A34A', '#0F766E', '#B45309', '#8B0000']
    colors = data.colors if data.colors else default_colors

    fig = go.Figure()

    for idx, (series_name, series_values) in enumerate(data.series.items()):
        fig.add_trace(go.Bar(
            x=data.labels,
            y=series_values,
            name=series_name,
            marker_color=colors[idx % len(colors)],
            hovertemplate='<b>%{x}</b><br>' + series_name + ': %{y:,.0f}<extra></extra>',
        ))

    fig.update_layout(
        title=data.title,
        xaxis_title=data.xlabel,
        yaxis_title=data.ylabel,
        barmode='group',
        bargap=0.25,
        bargroupgap=0.08,
        template="plotly_white",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return json.loads(graph_json)


def generate_evolution_chart(data: EvolutionData):
    """Génère un graphique d'évolution comparant période actuelle et précédente"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.labels,
        y=data.current,
        mode='lines+markers',
        name='Période actuelle',
        line=dict(color='#1A4D3A', width=3),
        marker=dict(size=8)
    ))
    
    if data.previous:
        fig.add_trace(go.Scatter(
            x=data.labels,
            y=data.previous,
            mode='lines+markers',
            name='Période précédente',
            line=dict(color='#8B0000', width=2.5, dash='dash'),
            marker=dict(size=7)
        ))
    
    fig.update_layout(
        title=data.title,
        xaxis_title="Période",
        yaxis_title=data.ylabel,
        template="plotly_white",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return json.loads(graph_json)


def generate_pie_chart(data: PieChartData):
    """Génère un graphique circulaire (camembert) au format Plotly JSON"""
    # Couleurs par défaut si non fournies
    colors = data.colors if data.colors else [
        '#1A4D3A', '#DC2626', '#2563EB', '#10B981', '#F59E0B',
        '#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#6366F1'
    ]
    
    # Répéter les couleurs si nécessaire
    while len(colors) < len(data.values):
        colors.extend(colors[:len(data.values) - len(colors)])
    colors = colors[:len(data.values)]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=data.labels,
            values=data.values,
            marker=dict(colors=colors, line=dict(color='#ffffff', width=1.5)),
            textinfo='none',
            hole=0.46,
            sort=False,
            direction='clockwise',
            domain=dict(x=[0.0, 0.46], y=[0.04, 0.96]),
            hovertemplate='<b>%{label}</b><br>Montant: %{value:,.1f} M FCFA<br>Part: %{percent}<extra></extra>',
        )
    ])

    fig.update_layout(
        title=data.title,
        template="plotly_white",
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=0.5,
            font=dict(size=11, color='#334155'),
            bgcolor='rgba(255,255,255,0)',
            borderwidth=0,
            itemsizing='constant',
            itemwidth=30,
            tracegroupgap=6,
        ),
        margin=dict(l=4, r=8, t=8, b=8),
        uniformtext=dict(minsize=10, mode='hide'),
    )
    
    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    return json.loads(graph_json)


def generate_chart_image(data: TimeSeriesData):
    """
    Génère un graphique matplotlib et le retourne comme image PNG encodée en base64
    Alternative pour ceux qui préfèrent matplotlib
    """
    plt.figure(figsize=(10, 6))
    plt.plot(data.labels, data.values, marker='o', linewidth=2, color='#1A4D3A')
    plt.title(data.title, fontsize=14, fontweight='bold')
    plt.xlabel("Période", fontsize=12)
    plt.ylabel(data.ylabel, fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Convertir en image base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"

