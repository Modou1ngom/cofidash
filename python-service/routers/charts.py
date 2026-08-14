"""
Router pour les endpoints de génération de graphiques
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import (
    TimeSeriesData,
    MultiSeriesData,
    BarChartData,
    GroupedBarData,
    EvolutionData,
    PieChartData,
)
from services.chart_service import (
    generate_timeseries_chart,
    generate_multiseries_chart,
    generate_bar_chart,
    generate_grouped_bar_chart,
    generate_evolution_chart,
    generate_pie_chart,
    generate_chart_image
)

router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.post("/timeseries")
async def create_timeseries_chart(data: TimeSeriesData):
    """
    Génère un graphique en ligne (time series) au format Plotly JSON
    """
    try:
        chart = generate_timeseries_chart(data)
        return JSONResponse(content={"chart": chart})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du graphique: {str(e)}")


@router.post("/multiseries")
async def create_multiseries_chart(data: MultiSeriesData):
    """
    Génère un graphique multi-séries au format Plotly JSON
    """
    try:
        chart = generate_multiseries_chart(data)
        return JSONResponse(content={"chart": chart})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du graphique: {str(e)}")


@router.post("/barchart")
async def create_bar_chart(data: BarChartData):
    """
    Génère un graphique en barres au format Plotly JSON
    """
    try:
        chart = generate_bar_chart(data)
        return JSONResponse(content={"chart": chart})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du graphique: {str(e)}")


@router.post("/groupedbar")
async def create_grouped_bar_chart(data: GroupedBarData):
    """
    Génère un graphique en barres groupées (ex. Objectif vs Réalisation)
    """
    try:
        chart = generate_grouped_bar_chart(data)
        return JSONResponse(content={"chart": chart})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du graphique groupé: {str(e)}")


@router.post("/evolution")
async def create_evolution_chart(data: EvolutionData):
    """
    Génère un graphique d'évolution comparant période actuelle et précédente
    """
    try:
        chart = generate_evolution_chart(data)
        return JSONResponse(content={"chart": chart})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du graphique: {str(e)}")


@router.post("/pie")
async def create_pie_chart(data: PieChartData):
    """
    Génère un graphique circulaire (camembert) au format Plotly JSON
    """
    try:
        chart = generate_pie_chart(data)
        return JSONResponse(content={"chart": chart})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du graphique circulaire: {str(e)}")


@router.post("/image")
async def create_chart_image(data: TimeSeriesData):
    """
    Génère un graphique matplotlib et le retourne comme image PNG encodée en base64
    Alternative pour ceux qui préfèrent matplotlib
    """
    try:
        image = generate_chart_image(data)
        return JSONResponse(content={"image": image})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de l'image: {str(e)}")

