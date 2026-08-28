"""
Modèles Pydantic pour les requêtes API
"""
from pydantic import BaseModel
from typing import List, Optional, Dict


class TimeSeriesData(BaseModel):
    labels: List[str]
    values: List[float]
    title: Optional[str] = "Évolution des données"
    ylabel: Optional[str] = "Valeur"


class MultiSeriesData(BaseModel):
    labels: List[str]
    series: Dict[str, List[float]]
    title: Optional[str] = "Graphique multi-séries"
    xlabel: Optional[str] = "Période"
    ylabel: Optional[str] = "Valeur"
    ylabel2: Optional[str] = None
    colors: Optional[List[str]] = None
    dual_axis: Optional[bool] = None


class BarChartData(BaseModel):
    labels: List[str]
    values: List[float]
    title: Optional[str] = "Graphique en barres"
    xlabel: Optional[str] = "Catégorie"
    ylabel: Optional[str] = "Valeur"
    colors: Optional[List[str]] = None


class GroupedBarData(BaseModel):
    labels: List[str]
    series: Dict[str, List[float]]
    title: Optional[str] = "Comparaison"
    xlabel: Optional[str] = "Catégorie"
    ylabel: Optional[str] = "Valeur"
    colors: Optional[List[str]] = None


class EvolutionData(BaseModel):
    labels: List[str]
    current: List[float]
    previous: Optional[List[float]] = None
    title: Optional[str] = "Évolution temporelle"
    ylabel: Optional[str] = "Valeur"


class PieChartData(BaseModel):
    labels: List[str]
    values: List[float]
    title: Optional[str] = "Graphique circulaire"
    colors: Optional[List[str]] = None

