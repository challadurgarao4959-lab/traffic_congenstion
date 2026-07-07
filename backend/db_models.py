# backend/models.py
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from datetime import datetime
from backend.database import Base

class TrafficEntry(Base):
    __tablename__ = "traffic_entries"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    vehicle_count = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)
    weather = Column(String(50), nullable=False) # Clear, Rainy, Snowy
    road_type = Column(String(50), nullable=False) # Highway, Arterial, Local
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0 to 6
    hour = Column(Integer, nullable=False) # 0 to 23
    is_weekend = Column(Integer, nullable=False) # 0 or 1
    is_holiday = Column(Boolean, default=False)
    congestion_score = Column(Float, nullable=False)
    congestion_level = Column(String(20), nullable=False) # Low, Medium, High
    co2_emissions = Column(Float, nullable=True) # Carbon footprint indicator

class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # Random Forest, XGBoost, etc.
    accuracy = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    r2_score = Column(Float, nullable=True)
    is_active = Column(Boolean, default=False)
    last_trained = Column(DateTime, default=datetime.utcnow)
    model_path = Column(String(255), nullable=True)

class SavedRoute(Base):
    __tablename__ = "saved_routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    start_point = Column(String(100), nullable=False)
    end_point = Column(String(100), nullable=False)
    distance_miles = Column(Float, nullable=False)
    base_duration_min = Column(Float, nullable=False)
    # Serialized JSON list of coordinates [[lat, lon], [lat, lon], ...]
    waypoints_json = Column(Text, nullable=False)
