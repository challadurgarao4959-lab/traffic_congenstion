# backend/crud.py
from sqlalchemy.orm import Session
from backend import db_models as models, schemas
from datetime import datetime
import json

# Traffic Entries
def get_traffic_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TrafficEntry).order_by(models.TrafficEntry.timestamp.desc()).offset(skip).limit(limit).all()

def create_traffic_entry(db: Session, entry: schemas.TrafficEntryCreate, derived_score: float, derived_level: str, co2: float):
    # Determine weekday/weekend and hour
    ts = entry.timestamp or datetime.now()
    hour = ts.hour
    day_of_week = ts.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    
    db_entry = models.TrafficEntry(
        timestamp=ts,
        vehicle_count=entry.vehicle_count,
        average_speed=entry.average_speed,
        weather=entry.weather,
        road_type=entry.road_type,
        latitude=entry.latitude,
        longitude=entry.longitude,
        day_of_week=day_of_week,
        hour=hour,
        is_weekend=is_weekend,
        is_holiday=entry.is_holiday,
        congestion_score=derived_score,
        congestion_level=derived_level,
        co2_emissions=co2
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def bulk_create_traffic_entries(db: Session, entries: list):
    db.bulk_insert_mappings(models.TrafficEntry, entries)
    db.commit()
    return len(entries)

def delete_all_traffic_entries(db: Session):
    db.query(models.TrafficEntry).delete()
    db.commit()

# ML Model Management
def get_ml_models(db: Session):
    return db.query(models.MLModel).all()

def get_active_model(db: Session):
    return db.query(models.MLModel).filter(models.MLModel.is_active == True).first()

def set_active_model(db: Session, name: str):
    # Deactivate all models
    db.query(models.MLModel).update({models.MLModel.is_active: False})
    # Activate the target model
    model = db.query(models.MLModel).filter(models.MLModel.name == name).first()
    if model:
        model.is_active = True
        db.commit()
        return model
    return None

def update_model_metrics(db: Session, name: str, metrics: dict, model_path: str):
    model = db.query(models.MLModel).filter(models.MLModel.name == name).first()
    if not model:
        model = models.MLModel(name=name)
        db.add(model)
    
    model.accuracy = metrics.get("Accuracy")
    model.f1_score = metrics.get("F1")
    model.rmse = metrics.get("RMSE")
    model.mae = metrics.get("MAE")
    model.r2_score = metrics.get("R2")
    model.model_path = model_path
    model.last_trained = datetime.utcnow()
    db.commit()
    db.refresh(model)
    return model

# Routes
def get_routes(db: Session):
    routes = db.query(models.SavedRoute).all()
    # If no routes exist, pre-populate with default hackathon sample routes
    if not routes:
        default_routes = [
            {
                "name": "Route Alpha (Main Expressway)",
                "start_point": "Downtown Hub",
                "end_point": "Tech Corridor Ext",
                "distance_miles": 5.2,
                "base_duration_min": 12.0,
                "waypoints_json": json.dumps([[40.7128, -74.0060], [40.7300, -74.0010], [40.7484, -73.9857]])
            },
            {
                "name": "Route Beta (Secondary Arterial)",
                "start_point": "Downtown Hub",
                "end_point": "Tech Corridor Ext",
                "distance_miles": 6.1,
                "base_duration_min": 15.0,
                "waypoints_json": json.dumps([[40.7128, -74.0060], [40.7380, -73.9900], [40.7484, -73.9857]])
            },
            {
                "name": "Route Gamma (Local Access Bypass)",
                "start_point": "Downtown Hub",
                "end_point": "Tech Corridor Ext",
                "distance_miles": 7.4,
                "base_duration_min": 20.0,
                "waypoints_json": json.dumps([[40.7128, -74.0060], [40.7200, -73.9700], [40.7400, -73.9750], [40.7484, -73.9857]])
            }
        ]
        for dr in default_routes:
            db_route = models.SavedRoute(**dr)
            db.add(db_route)
        db.commit()
        routes = db.query(models.SavedRoute).all()
    return routes

def create_route(db: Session, route: schemas.SavedRouteCreate):
    db_route = models.SavedRoute(
        name=route.name,
        start_point=route.start_point,
        end_point=route.end_point,
        distance_miles=route.distance_miles,
        base_duration_min=route.base_duration_min,
        waypoints_json=route.waypoints_json
    )
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route
