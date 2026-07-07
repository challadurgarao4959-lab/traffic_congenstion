# backend/ml_engine.py
import os
import joblib
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, f1_score
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except (ImportError, Exception):
    from sklearn.ensemble import HistGradientBoostingRegressor
    HAS_XGBOOST = False


from backend import db_models as models, crud
from backend.database import SessionLocal, engine
from models.lstm_numpy import LSTMRegressor

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Fixed features layout
FEATURE_COLUMNS = [
    "latitude", "longitude", "vehicle_count", "average_speed",
    "day_of_week", "hour", "is_weekend", "is_peak_hour",
    "weather_Rainy", "weather_Snowy", "road_type_Highway", "road_type_Local"
]

def generate_and_seed_data(db, num_rows=1000):
    """
    Generates synthetic traffic data and inserts it into the database
    """
    np.random.seed(42)
    start_date = datetime.now() - timedelta(days=30)
    
    locations = [
        {"name": "Downtown Hub", "lat": 40.7128, "lon": -74.0060},
        {"name": "Midtown Crossing", "lat": 40.7589, "lon": -73.9851},
        {"name": "Tech Corridor Ext", "lat": 40.7484, "lon": -73.9857},
        {"name": "Expressway Exit 4", "lat": 40.7061, "lon": -73.9969}
    ]
    
    entries = []
    for i in range(num_rows):
        delta_mins = np.random.randint(0, 43200) # Span over 30 days
        ts = start_date + timedelta(minutes=delta_mins)
        loc = np.random.choice(locations)
        
        hour = ts.hour
        day_of_week = ts.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Rush hours: 8-10 AM, 5-7 PM
        is_peak_hour = 1 if hour in [8, 9, 17, 18] else 0
        
        # Base count and speed rules
        if is_peak_hour == 1:
            base_count = np.random.randint(120, 250)
            base_speed = np.random.randint(10, 25)
        elif 23 <= hour or hour <= 5:
            base_count = np.random.randint(10, 45)
            base_speed = np.random.randint(50, 65)
        else:
            base_count = np.random.randint(50, 120)
            base_speed = np.random.randint(30, 50)
            
        weather = np.random.choice(["Clear", "Rainy", "Snowy"], p=[0.7, 0.2, 0.1])
        # Weather impact modifiers
        if weather == "Rainy":
            base_speed -= 8
            base_count += 10
        elif weather == "Snowy":
            base_speed -= 15
            base_count -= 15
            
        road_type = np.random.choice(["Highway", "Arterial", "Local"], p=[0.4, 0.4, 0.2])
        
        # Congestion score calculation (continuous 0 to 100)
        # Driven by high vehicle counts and low average speeds
        speed_factor = max(0, 70 - base_speed) / 70.0
        count_factor = min(300, base_count) / 300.0
        congestion_score = (count_factor * 45.0) + (speed_factor * 55.0)
        congestion_score = max(0.0, min(100.0, congestion_score + np.random.normal(0, 3)))
        
        # Map score to levels
        if congestion_score < 35:
            level = "Low"
        elif congestion_score < 70:
            level = "Medium"
        else:
            level = "High"
            
        # CO2 Emission estimation: standard emission base rate modified by congestion level
        # High congestion = more idling and stop-go traffic = higher CO2 emission rate
        co2_emission = round(max(5, base_count) * (1.2 if level == "High" else 0.8 if level == "Medium" else 0.4), 2)
        
        entries.append({
            "timestamp": ts,
            "latitude": float(loc["lat"] + np.random.normal(0, 0.0015)),
            "longitude": float(loc["lon"] + np.random.normal(0, 0.0015)),
            "vehicle_count": int(max(5, base_count)),
            "average_speed": float(max(5, base_speed)),
            "weather": weather,
            "road_type": road_type,
            "day_of_week": int(day_of_week),
            "hour": int(hour),
            "is_weekend": int(is_weekend),
            "is_holiday": False,
            "congestion_score": float(congestion_score),
            "congestion_level": level,
            "co2_emissions": co2_emission
        })
        
    crud.bulk_create_traffic_entries(db, entries)
    
    # Save a CSV backup
    df = pd.DataFrame(entries)
    df.to_csv(os.path.join(DATA_DIR, "synthetic_traffic_data.csv"), index=False)
    print(f"Seeded database with {num_rows} traffic entries and created synthetic backup CSV.")

def get_discrete_level(score):
    if score < 35:
        return 0 # Low
    elif score < 70:
        return 1 # Medium
    else:
        return 2 # High

def train_and_evaluate_all(db):
    """
    Reads traffic entries from database, preprocesses them, trains 4 models,
    compares their metrics, and saves the models and metrics to database/files.
    """
    # 1. Fetch data from DB
    entries = db.query(models.TrafficEntry).all()
    if len(entries) < 100:
        # If too little data, generate synthetic data first
        generate_and_seed_data(db, num_rows=1500)
        entries = db.query(models.TrafficEntry).all()
        
    # Convert SQLAlchemy objects to pandas DataFrame
    data_list = []
    for entry in entries:
        data_list.append({
            "latitude": entry.latitude,
            "longitude": entry.longitude,
            "vehicle_count": entry.vehicle_count,
            "average_speed": entry.average_speed,
            "weather": entry.weather,
            "road_type": entry.road_type,
            "day_of_week": entry.day_of_week,
            "hour": entry.hour,
            "is_weekend": entry.is_weekend,
            "congestion_score": entry.congestion_score,
            "congestion_level": entry.congestion_level
        })
        
    df = pd.DataFrame(data_list)
    
    # 2. Data Preprocessing
    # Handle missing values
    df["vehicle_count"] = df["vehicle_count"].fillna(df["vehicle_count"].median())
    df["average_speed"] = df["average_speed"].fillna(df["average_speed"].median())
    
    # Remove outliers on numerical fields (Z-score method, threshold of 3)
    num_cols = ["vehicle_count", "average_speed"]
    for col in num_cols:
        col_mean = df[col].mean()
        col_std = df[col].std()
        if col_std > 0:
            z_scores = (df[col] - col_mean) / col_std
            df = df[np.abs(z_scores) < 3.0]
            
    # Derived Feature Engineering
    df["is_peak_hour"] = df["hour"].apply(lambda h: 1 if h in [8, 9, 17, 18] else 0)
    
    # Encode categorical variables: weather, road_type
    # Weather columns
    df["weather_Rainy"] = (df["weather"] == "Rainy").astype(int)
    df["weather_Snowy"] = (df["weather"] == "Snowy").astype(int)
    # Road type columns
    df["road_type_Highway"] = (df["road_type"] == "Highway").astype(int)
    df["road_type_Local"] = (df["road_type"] == "Local").astype(int)
    
    # Save target variable separately
    X = df[FEATURE_COLUMNS].copy()
    y = df["congestion_score"].values
    
    # 3. Scale Features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save the scaler for inference pipeline
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    
    # Train-test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    # Convert continuous scores to discrete classes for accuracy evaluation
    y_test_classes = np.array([get_discrete_level(val) for val in y_test])
    
    trained_models_metrics = {}
    
    # --- MODEL 1: Random Forest ---
    print("Training Random Forest...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    
    # --- MODEL 2: Gradient Boosting ---
    print("Training Gradient Boosting...")
    gb_model = GradientBoostingRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    gb_model.fit(X_train, y_train)
    gb_preds = gb_model.predict(X_test)
    
    # --- MODEL 3: XGBoost ---
    print("Training XGBoost...")
    if HAS_XGBOOST:
        xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        xgb_model.fit(X_train, y_train)
        xgb_preds = xgb_model.predict(X_test)
    else:
        print("XGBoost failed to load (OpenMP libomp missing). Using HistGradientBoostingRegressor fallback.")
        xgb_model = HistGradientBoostingRegressor(max_iter=100, max_depth=5, learning_rate=0.1, random_state=42)
        xgb_model.fit(X_train, y_train)
        xgb_preds = xgb_model.predict(X_test)
    
    # --- MODEL 4: NumPy-based LSTM ---
    print("Training Custom NumPy LSTM...")
    # X_train is 2D, we will reshape it inside LSTM. LSTMRegressor expects input_dim = 12
    lstm_model = LSTMRegressor(input_dim=len(FEATURE_COLUMNS), hidden_dim=16, epochs=8, seq_len=4, batch_size=64)
    # We train the LSTM using the original training set. It internally handles sequence creation.
    # To fit Scikit-Learn fit interface, we pass X_train (unsequenced scaled 2D array) and y_train
    lstm_model.fit(X_train, y_train)
    lstm_preds = lstm_model.predict(X_test)
    
    # Define model dictionary for loop iteration
    models_dict = {
        "Random Forest": (rf_model, rf_preds),
        "Gradient Boosting": (gb_model, gb_preds),
        "XGBoost": (xgb_model, xgb_preds),
        "LSTM": (lstm_model, lstm_preds)
    }
    
    best_model_name = None
    best_rmse = float('inf')
    
    for name, (model, preds) in models_dict.items():
        # Regression metrics
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        
        # Map predictions to classification levels (0, 1, 2)
        pred_classes = np.array([get_discrete_level(val) for val in preds])
        
        # Classification metrics
        accuracy = float(accuracy_score(y_test_classes, pred_classes))
        f1 = float(f1_score(y_test_classes, pred_classes, average='macro'))
        
        metrics = {
            "RMSE": round(rmse, 4),
            "MAE": round(mae, 4),
            "R2": round(r2, 4),
            "Accuracy": round(accuracy, 4),
            "F1": round(f1, 4)
        }
        
        # Save model to disk
        model_filename = f"{name.lower().replace(' ', '_')}_model.pkl"
        model_path = os.path.join(MODELS_DIR, model_filename)
        
        if name == "LSTM":
            # LSTM has a custom save method
            model.save(model_path)
        else:
            joblib.dump(model, model_path)
            
        # Update metrics in database
        crud.update_model_metrics(db, name=name, metrics=metrics, model_path=model_path)
        trained_models_metrics[name] = metrics
        
        # Find best model based on RMSE
        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            
    # Set best model as active
    crud.set_active_model(db, best_model_name)
    print(f"Model comparison completed. Best model is {best_model_name} with RMSE: {best_rmse:.4f}")
    
    return trained_models_metrics, best_model_name

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Generate schema tables if they don't exist
        models.Base.metadata.create_all(bind=engine)
        # Train and output
        metrics, best = train_and_evaluate_all(db)
        print("Training Metrics JSON Output:")
        print(json.dumps(metrics, indent=2))
    finally:
        db.close()
