# backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Traffic Data schemas
class TrafficEntryBase(BaseModel):
    timestamp: datetime
    vehicle_count: int
    average_speed: float
    weather: str
    road_type: str
    latitude: float
    longitude: float
    day_of_week: int
    hour: int
    is_weekend: int
    is_holiday: bool = False
    congestion_score: float
    congestion_level: str
    co2_emissions: Optional[float] = None

class TrafficEntryCreate(BaseModel):
    timestamp: Optional[datetime] = None
    vehicle_count: int = Field(..., ge=0)
    average_speed: float = Field(..., ge=0)
    weather: str # Clear, Rainy, Snowy
    road_type: str # Highway, Arterial, Local
    latitude: float
    longitude: float
    is_holiday: bool = False

class TrafficEntryResponse(TrafficEntryBase):
    id: int

    class Config:
        from_attributes = True

# ML Model schemas
class MLModelResponse(BaseModel):
    id: int
    name: str
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    is_active: bool
    last_trained: datetime
    model_path: Optional[str] = None

    class Config:
        from_attributes = True

# Route schemas
class SavedRouteBase(BaseModel):
    name: str
    start_point: str
    end_point: str
    distance_miles: float
    base_duration_min: float
    waypoints_json: str

class SavedRouteCreate(SavedRouteBase):
    pass

class SavedRouteResponse(SavedRouteBase):
    id: int

    class Config:
        from_attributes = True

# Predict Requests & Responses
class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    vehicle_count: int = Field(..., ge=0)
    average_speed: float = Field(..., ge=0)
    weather: str
    road_type: str
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: int = Field(..., ge=0, le=1)
    is_holiday: bool = False
    model_name: Optional[str] = None # Optional selection

class PredictionResponse(BaseModel):
    congestion_score: float
    congestion_level: str
    co2_emissions: float
    model_used: str
    timestamp: datetime

# Route Advisor schemas
class RouteOption(BaseModel):
    name: str
    distance: float
    base_time: float
    predicted_congestion: float
    predicted_level: str
    adjusted_time: float
    co2_emissions: float
    waypoints: List[List[float]] # [[lat, lon], ...]
    is_fastest: bool = False
    is_least_congested: bool = False
    time_saved_min: float = 0.0

class AdvisorRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    vehicle_count: int = Field(85, ge=0)
    average_speed: float = Field(42, ge=0)
    weather: str = "Clear"
    road_type: str = "Highway"

class AdvisorResponse(BaseModel):
    start_point: str
    end_point: str
    routes: List[RouteOption]
    recommendation: str

# Dashboard Analytics schemas
class HourlyCongestion(BaseModel):
    hour: int
    avg_score: float

class WeatherImpact(BaseModel):
    weather: str
    avg_score: float
    avg_speed: float

class RoadTypeImpact(BaseModel):
    road_type: str
    avg_score: float
    avg_speed: float

class DashboardStats(BaseModel):
    total_records: int
    avg_congestion: float
    active_alerts: List[str]
    hourly_trends: List[HourlyCongestion]
    weather_impact: List[WeatherImpact]
    road_impact: List[RoadTypeImpact]
