# utils/helpers.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import joblib
import os

def generate_synthetic_data(num_rows=5000):
    np.random.seed(42)
    start_date = datetime(2026, 1, 1)
    
    data = []
    # Major intersections / Lat-Long clusters
    locations = [
        {"name": "Downtown Hub", "lat": 40.7128, "lon": -74.0060},
        {"name": "Midtown Crossing", "lat": 40.7589, "lon": -73.9851},
        {"name": "Tech Corridor Ext", "lat": 40.7484, "lon": -73.9857},
        {"name": "Expressway Exit 4", "lat": 40.7061, "lon": -73.9969}
    ]
    
    for i in range(num_rows):
        delta_mins = np.random.randint(0, 43200) # Span over a month
        ts = start_date + timedelta(minutes=delta_mins)
        loc = np.random.choice(locations)
        
        hour = ts.hour
        day_of_week = ts.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Base traffic logic (Rush hours: 8-10 AM, 5-7 PM)
        if hour in [8, 9, 17, 18]:
            base_count = np.random.randint(120, 250)
            base_speed = np.random.randint(10, 25)
        elif 23 <= hour or hour <= 5:
            base_count = np.random.randint(10, 45)
            base_speed = np.random.randint(50, 65)
        else:
            base_count = np.random.randint(50, 120)
            base_speed = np.random.randint(30, 50)
            
        weather = np.random.choice(["Clear", "Rainy", "Snowy"], p=[0.7, 0.2, 0.1])
        # Weather modifiers
        if weather == "Rainy":
            base_speed -= 8
            base_count += 10
        elif weather == "Snowy":
            base_speed -= 15
            base_count -= 15
            
        road_type = np.random.choice(["Highway", "Arterial", "Local"], p=[0.4, 0.4, 0.2])
        
        # Derived Target: Congestion Score (0 to 100)
        # Higher vehicle counts and lower speeds drive congestion up
        congestion_score = (base_count * 0.4) + ((65 - base_speed) * 0.6)
        congestion_score = max(0, min(100, congestion_score)) # Clamp
        
        data.append({
            "timestamp": ts,
            "latitude": loc["lat"] + np.random.normal(0, 0.002),
            "longitude": loc["lon"] + np.random.normal(0, 0.002),
            "vehicle_count": max(5, base_count),
            "average_speed": max(5, base_speed),
            "weather": weather,
            "road_type": road_type,
            "day_of_week": day_of_week,
            "hour": hour,
            "is_weekend": is_weekend,
            "congestion_score": congestion_score
        })
        
    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/synthetic_traffic_data.csv', index=False)
    print("Synthetic data saved to data/synthetic_traffic_data.csv")
    return df

def train_model():
    if not os.path.exists('data/synthetic_traffic_data.csv'):
        df = generate_synthetic_data()
    else:
        df = pd.read_csv('data/synthetic_traffic_data.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # Preprocessing & Feature Engineering
    df = pd.get_dummies(df, columns=['weather', 'road_type'], drop_first=True)
    
    # Feature Selection
    features = [c for c in df.columns if c not in ['timestamp', 'congestion_score']]
    X = df[features]
    y = df['congestion_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Model: XGBoost Regressor
    model = xgb.XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.08, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    
    metrics = {
        "RMSE": root_mean_squared_error(y_test, preds),
        "MAE": mean_absolute_error(y_test, preds),
        "R2": r2_score(y_test, preds)
    }
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/xgboost_traffic_model.pkl')
    # Save features blueprint
    joblib.dump(features, 'models/model_features.pkl')
    
    print("Model Training Metrics:", metrics)
    return metrics

if __name__ == "__main__":
    train_model()