# backend/router.py
import os
import io
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend import db_models as models, schemas, crud, ml_engine
from backend.database import get_db
from models.lstm_numpy import LSTMRegressor

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Helper to load a model by name
def load_ml_model(name: str):
    filename = f"{name.lower().replace(' ', '_')}_model.pkl"
    filepath = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    if "lstm" in name.lower():
        return LSTMRegressor.load(filepath)
    else:
        return joblib.load(filepath)

# Helper to load the scaler
def load_scaler():
    filepath = os.path.join(MODELS_DIR, "scaler.pkl")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Scaler file not found: {filepath}")
    return joblib.load(filepath)

# Helper for preprocessing single prediction payloads
def preprocess_payload(payload: schemas.PredictionRequest, scaler):
    # Derive peak hour indicator (8-10 AM, 5-7 PM)
    is_peak = 1 if payload.hour in [8, 9, 17, 18] else 0
    
    # Construct matching input dict
    input_data = {
        "latitude": [payload.latitude],
        "longitude": [payload.longitude],
        "vehicle_count": [payload.vehicle_count],
        "average_speed": [payload.average_speed],
        "day_of_week": [payload.day_of_week],
        "hour": [payload.hour],
        "is_weekend": [payload.is_weekend],
        "is_peak_hour": [is_peak],
        "weather_Rainy": [1 if payload.weather == "Rainy" else 0],
        "weather_Snowy": [1 if payload.weather == "Snowy" else 0],
        "road_type_Highway": [1 if payload.road_type == "Highway" else 0],
        "road_type_Local": [1 if payload.road_type == "Local" else 0]
    }
    
    df_input = pd.DataFrame(input_data)
    # Align columns
    df_input = df_input[ml_engine.FEATURE_COLUMNS]
    
    # Scale
    scaled_array = scaler.transform(df_input)
    return scaled_array

# --- 1. Traffic Data Management ---

@router.get("/traffic/data", response_model=List[schemas.TrafficEntryResponse])
def read_traffic_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_traffic_entries(db, skip=skip, limit=limit)

@router.post("/traffic/data", response_model=schemas.TrafficEntryResponse)
def add_traffic_data(payload: schemas.TrafficEntryCreate, db: Session = Depends(get_db)):
    # Quick dynamic prediction using simple heuristic if model not trained
    try:
        active_model = crud.get_active_model(db)
        if active_model:
            scaler = load_scaler()
            model = load_ml_model(active_model.name)
            # Reconstruct prediction request
            now = payload.timestamp or datetime.now()
            pred_req = schemas.PredictionRequest(
                latitude=payload.latitude,
                longitude=payload.longitude,
                vehicle_count=payload.vehicle_count,
                average_speed=payload.average_speed,
                weather=payload.weather,
                road_type=payload.road_type,
                hour=now.hour,
                day_of_week=now.weekday(),
                is_weekend=1 if now.weekday() >= 5 else 0,
                is_holiday=payload.is_holiday
            )
            scaled_input = preprocess_payload(pred_req, scaler)
            score = float(model.predict(scaled_input)[0])
        else:
            raise Exception("No active model")
    except:
        # Heuristic fallback
        speed_factor = max(0, 70 - payload.average_speed) / 70.0
        count_factor = min(300, payload.vehicle_count) / 300.0
        score = (count_factor * 45.0) + (speed_factor * 55.0)
        
    score = max(0.0, min(100.0, score))
    level = "Low" if score < 35 else "Medium" if score < 70 else "High"
    co2 = round(payload.vehicle_count * (1.2 if level == "High" else 0.8 if level == "Medium" else 0.4), 2)
    
    return crud.create_traffic_entry(db, payload, derived_score=score, derived_level=level, co2=co2)

@router.post("/traffic/upload")
async def upload_traffic_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    # Required CSV columns verification
    required_cols = ["timestamp", "vehicle_count", "average_speed", "weather", "road_type", "latitude", "longitude"]
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing required column in CSV: {col}")
            
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Fill defaults
    df["is_holiday"] = df.get("is_holiday", False).astype(bool)
    
    entries = []
    for _, row in df.iterrows():
        ts = row["timestamp"]
        hour = ts.hour
        day_of_week = ts.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Heuristic fallback for dataset rows that don't have congestion scores pre-computed
        if "congestion_score" in df.columns:
            score = float(row["congestion_score"])
        else:
            speed_factor = max(0, 70 - float(row["average_speed"])) / 70.0
            count_factor = min(300, int(row["vehicle_count"])) / 300.0
            score = (count_factor * 45.0) + (speed_factor * 55.0)
            
        score = max(0.0, min(100.0, score))
        level = "Low" if score < 35 else "Medium" if score < 70 else "High"
        co2 = round(int(row["vehicle_count"]) * (1.2 if level == "High" else 0.8 if level == "Medium" else 0.4), 2)
        
        entries.append({
            "timestamp": ts,
            "vehicle_count": int(row["vehicle_count"]),
            "average_speed": float(row["average_speed"]),
            "weather": str(row["weather"]),
            "road_type": str(row["road_type"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "day_of_week": int(day_of_week),
            "hour": int(hour),
            "is_weekend": int(is_weekend),
            "is_holiday": bool(row["is_holiday"]),
            "congestion_score": score,
            "congestion_level": level,
            "co2_emissions": co2
        })
        
    inserted_count = crud.bulk_create_traffic_entries(db, entries)
    return {"message": f"Successfully uploaded and imported {inserted_count} traffic entries."}

@router.post("/traffic/simulate")
def simulate_traffic_stream(db: Session = Depends(get_db)):
    """
    Simulates real-time updates for key locations in our database
    """
    import random
    locations = crud.get_routes(db)  # We can extract coordinate points
    weather = random.choice(["Clear", "Rainy", "Snowy"])
    road_type = random.choice(["Highway", "Arterial", "Local"])
    
    simulated_entries = []
    # Major junctions coordinates
    junctions = [
        {"lat": 40.7128, "lon": -74.0060, "name": "Downtown Interchange"},
        {"lat": 40.7589, "lon": -73.9851, "name": "Midtown Tunnel Exit"},
        {"lat": 40.7484, "lon": -73.9857, "name": "Empire Bypass"},
        {"lat": 40.7061, "lon": -73.9969, "name": "Brooklyn Bridge Inflow"}
    ]
    
    now = datetime.now()
    hour = now.hour
    is_peak = 1 if hour in [8, 9, 17, 18] else 0
    
    for junc in junctions:
        if is_peak:
            vehicle_count = random.randint(150, 280)
            average_speed = random.randint(8, 22)
        else:
            vehicle_count = random.randint(35, 110)
            average_speed = random.randint(35, 58)
            
        # Add random variations
        if weather == "Rainy":
            average_speed = max(5, average_speed - 8)
            vehicle_count += random.randint(5, 15)
        elif weather == "Snowy":
            average_speed = max(5, average_speed - 15)
            vehicle_count = max(5, vehicle_count - random.randint(10, 20))
            
        entry_create = schemas.TrafficEntryCreate(
            timestamp=now,
            vehicle_count=vehicle_count,
            average_speed=average_speed,
            weather=weather,
            road_type=road_type,
            latitude=junc["lat"],
            longitude=junc["lon"],
            is_holiday=False
        )
        
        # Save to DB
        entry_res = add_traffic_data(entry_create, db)
        simulated_entries.append(entry_res)
        
    return {"message": "Simulated dynamic traffic flow", "data": simulated_entries}

@router.get("/gender")
def get_gender_data():
    gender_file = os.path.join(BASE_DIR, "gender.json")
    if not os.path.exists(gender_file):
        raise HTTPException(status_code=404, detail="Gender data file not found.")
    with open(gender_file, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/routes", response_model=List[schemas.SavedRouteResponse])
def list_saved_routes(db: Session = Depends(get_db)):
    return crud.get_routes(db)

@router.post("/traffic/clear")
def clear_traffic_entries(db: Session = Depends(get_db)):
    crud.delete_all_traffic_entries(db)
    return {"message": "Cleared all historical traffic records."}


# --- 2. ML Engine & Predictions ---

@router.post("/predict", response_model=schemas.PredictionResponse)
def predict_congestion(payload: schemas.PredictionRequest, db: Session = Depends(get_db)):
    # 1. Determine which model to use
    model_name = payload.model_name
    if not model_name:
        active = crud.get_active_model(db)
        if not active:
            raise HTTPException(status_code=400, detail="No active model found. Train models first.")
        model_name = active.name
        
    try:
        scaler = load_scaler()
        model = load_ml_model(model_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load prediction assets: {str(e)}")
        
    try:
        # Preprocess
        scaled_input = preprocess_payload(payload, scaler)
        
        # Predict continuous score
        score = float(model.predict(scaled_input)[0])
        score = max(0.0, min(100.0, score)) # Clamp boundaries
        
        # Determine discrete level
        if score < 35:
            level = "Low"
        elif score < 70:
            level = "Medium"
        else:
            level = "High"
            
        # CO2 emissions estimation
        co2 = round(payload.vehicle_count * (1.2 if level == "High" else 0.8 if level == "Medium" else 0.4), 2)
        
        return schemas.PredictionResponse(
            congestion_score=round(score, 2),
            congestion_level=level,
            co2_emissions=co2,
            model_used=model_name,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/predict/compare", response_model=List[schemas.MLModelResponse])
def compare_models(db: Session = Depends(get_db)):
    return crud.get_ml_models(db)

@router.post("/models/train")
def train_models(db: Session = Depends(get_db)):
    try:
        metrics, best_model = ml_engine.train_and_evaluate_all(db)
        return {
            "message": f"Successfully completed training for all models. Best model: {best_model}",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training pipeline execution failed: {str(e)}")

@router.post("/models/select")
def select_model(name: str, db: Session = Depends(get_db)):
    model = crud.set_active_model(db, name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found. Please train models first.")
    return {"message": f"Successfully set {name} as the active predictive model."}


# --- 3. Smart Route Advisor ---

@router.post("/routes/advisor", response_model=schemas.AdvisorResponse)
def smart_route_advisor(payload: schemas.AdvisorRequest, db: Session = Depends(get_db)):
    """
    Takes start/end coordinate markers, queries all preset routes, uses the ML engine to forecast
    congestion for each route options, and presents optimization choices (fastest, greenest, etc.)
    """
    routes = crud.get_routes(db)
    if not routes:
        raise HTTPException(status_code=404, detail="No route options found in the system.")
        
    route_options = []
    
    # Load model and scaler for congestion predictions along routes
    active_model = crud.get_active_model(db)
    model, scaler = None, None
    if active_model:
        try:
            model = load_ml_model(active_model.name)
            scaler = load_scaler()
        except:
            pass
            
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    
    for route in routes:
        waypoints = json.loads(route.waypoints_json)
        # Calculate coordinates midpoint to represent localization anchor
        m_idx = len(waypoints) // 2
        mid_lat, mid_lon = waypoints[m_idx][0], waypoints[m_idx][1]
        
        # Vehicle count modifier based on route classification
        # Expressway has higher volume capacity than Local bypasses
        mod_vehicle_count = payload.vehicle_count
        if "Local" in route.name:
            mod_vehicle_count = int(payload.vehicle_count * 0.4)
        elif "Secondary" in route.name:
            mod_vehicle_count = int(payload.vehicle_count * 0.7)
            
        pred_score = 45.0 # default fallback
        pred_level = "Medium"
        
        if model and scaler:
            # Reconstruct prediction request
            pred_req = schemas.PredictionRequest(
                latitude=mid_lat,
                longitude=mid_lon,
                vehicle_count=mod_vehicle_count,
                average_speed=payload.average_speed,
                weather=payload.weather,
                road_type="Highway" if "Expressway" in route.name else "Local" if "Local" in route.name else "Arterial",
                hour=hour,
                day_of_week=day_of_week,
                is_weekend=is_weekend
            )
            try:
                scaled_inp = preprocess_payload(pred_req, scaler)
                pred_score = float(model.predict(scaled_inp)[0])
                pred_score = max(0.0, min(100.0, pred_score))
                pred_level = "Low" if pred_score < 35 else "Medium" if pred_score < 70 else "High"
            except:
                pass
                
        # Calculate time adjustment factor: higher congestion = lower speed = longer travel duration
        # At 100 congestion, speed drops, base time triples
        multiplier = 1.0 + (pred_score / 50.0)
        adjusted_time = round(route.base_duration_min * multiplier, 2)
        
        # Calculate emissions
        co2 = round(mod_vehicle_count * (1.2 if pred_level == "High" else 0.8 if pred_level == "Medium" else 0.4) * (adjusted_time / 60.0), 2)
        
        route_options.append({
            "name": route.name,
            "distance": route.distance_miles,
            "base_time": route.base_duration_min,
            "predicted_congestion": round(pred_score, 2),
            "predicted_level": pred_level,
            "adjusted_time": adjusted_time,
            "co2_emissions": co2,
            "waypoints": waypoints
        })
        
    if not route_options:
        raise HTTPException(status_code=500, detail="Failed to construct route advisories.")
        
    # Mark Fastest & Least Congested
    min_time_idx = min(range(len(route_options)), key=lambda idx: route_options[idx]["adjusted_time"])
    min_cong_idx = min(range(len(route_options)), key=lambda idx: route_options[idx]["predicted_congestion"])
    
    route_options[min_time_idx]["is_fastest"] = True
    route_options[min_cong_idx]["is_least_congested"] = True
    
    # Calculate time saved relative to the slowest route
    max_time = max(r["adjusted_time"] for r in route_options)
    for r in route_options:
        r["time_saved_min"] = round(max_time - r["adjusted_time"], 2)
        
    best_opt = route_options[min_time_idx]
    rec_string = f"💡 **Recommended Route:** Use **{best_opt['name']}**. Est. travel time is {best_opt['adjusted_time']} minutes, saving you up to {best_opt['time_saved_min']} minutes compared to other bottleneck lanes."
    
    return schemas.AdvisorResponse(
        start_point="Downtown Hub",
        end_point="Tech Corridor Ext",
        routes=[schemas.RouteOption(**ro) for ro in route_options],
        recommendation=rec_string
    )


# --- 4. Dashboard Visual Analytics ---

@router.get("/analytics/dashboard", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Aggregates analytical metrics for the frontend visualizations
    """
    total = db.query(models.TrafficEntry).count()
    if total == 0:
        # Return mock defaults or generate synthetic data
        return schemas.DashboardStats(
            total_records=0,
            avg_congestion=0.0,
            active_alerts=[],
            hourly_trends=[],
            weather_impact=[],
            road_impact=[]
        )
        
    avg_score_query = db.query(models.TrafficEntry.congestion_score).all()
    avg_score = float(np.mean([x[0] for x in avg_score_query]))
    
    # Alert heuristics based on current conditions
    recent_entries = db.query(models.TrafficEntry).order_by(models.TrafficEntry.timestamp.desc()).limit(5).all()
    alerts = []
    
    high_count = sum(1 for e in recent_entries if e.congestion_level == "High")
    if high_count >= 2:
        alerts.append("🔴 Alert: Heavy traffic cluster detected. Speeds average under 15 mph.")
        alerts.append("💡 Smart Advice: Route Gamma (Local Access Bypass) can save 14 minutes right now.")
    else:
        alerts.append("🟢 System Normal: Moderate traffic volume observed across the network.")
        alerts.append("💡 Eco Tip: Keeping speeds near 45 mph optimizes carbon output.")
        
    # 1. Hourly congestion averages
    hourly_data = db.query(
        models.TrafficEntry.hour,
        models.TrafficEntry.congestion_score
    ).all()
    df_h = pd.DataFrame(hourly_data, columns=["hour", "score"])
    h_trends = df_h.groupby("hour")["score"].mean().reset_index().to_dict(orient="records")
    h_trends_schemas = [schemas.HourlyCongestion(hour=int(row["hour"]), avg_score=float(row["score"])) for row in h_trends]
    
    # 2. Weather impact
    weather_data = db.query(
        models.TrafficEntry.weather,
        models.TrafficEntry.congestion_score,
        models.TrafficEntry.average_speed
    ).all()
    df_w = pd.DataFrame(weather_data, columns=["weather", "score", "speed"])
    w_impact = df_w.groupby("weather").agg({"score": "mean", "speed": "mean"}).reset_index().to_dict(orient="records")
    w_impact_schemas = [schemas.WeatherImpact(
        weather=row["weather"],
        avg_score=float(row["score"]),
        avg_speed=float(row["speed"])
    ) for row in w_impact]
    
    # 3. Road class impact
    road_data = db.query(
        models.TrafficEntry.road_type,
        models.TrafficEntry.congestion_score,
        models.TrafficEntry.average_speed
    ).all()
    df_r = pd.DataFrame(road_data, columns=["road_type", "score", "speed"])
    r_impact = df_r.groupby("road_type").agg({"score": "mean", "speed": "mean"}).reset_index().to_dict(orient="records")
    r_impact_schemas = [schemas.RoadTypeImpact(
        road_type=row["road_type"],
        avg_score=float(row["score"]),
        avg_speed=float(row["speed"])
    ) for row in r_impact]
    
    return schemas.DashboardStats(
        total_records=total,
        avg_congestion=round(avg_score, 2),
        active_alerts=alerts,
        hourly_trends=h_trends_schemas,
        weather_impact=w_impact_schemas,
        road_impact=r_impact_schemas
    )
