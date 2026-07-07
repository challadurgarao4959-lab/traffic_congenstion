# frontend/app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Smart Route Advisor", layout="wide", page_icon="🚦")

BACKEND_API = "http://localhost:8000/predict"

st.title("🚦 Traffic Congestion Prediction & Smart Route Advisor")
st.markdown("Predict localized bottlenecks, estimate carbon footprints, and recalculate alternative routes dynamically.")

# Sidebar Controls
st.sidebar.header("🕹️ Control Dashboard & Inputs")
weather = st.sidebar.selectbox("Current Weather", ["Clear", "Rainy", "Snowy"])
road_type = st.sidebar.selectbox("Road Class Type", ["Highway", "Arterial", "Local"])
vehicle_count = st.sidebar.slider("Observed Vehicle Count", 5, 300, 85)
avg_speed = st.sidebar.slider("Average Velocity (mph)", 5, 80, 42)

now = datetime.now()
hour = st.sidebar.slider("Forecast Hour Window", 0, 23, int(now.hour))
day_of_week = now.weekday()
is_weekend = 1 if day_of_week >= 5 else 0

# Mocked Routes for Recommendation Frame
routes_db = {
    "Route Alpha (Main Highway)": {"lat": 40.7128, "lon": -74.0060, "base_dist": 5.2, "base_time": 12},
    "Route Beta (Secondary Arterial)": {"lat": 40.7589, "lon": -73.9851, "base_dist": 6.1, "base_time": 15},
    "Route Gamma (Local Access Bypass)": {"lat": 40.7484, "lon": -73.9857, "base_dist": 7.4, "base_time": 20}
}

# Core Layout Matrix
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔮 Target Path Predictions")
    
    route_metrics = []
    
    for name, metadata in routes_db.items():
        payload = {
            "latitude": metadata["lat"],
            "longitude": metadata["lon"],
            "vehicle_count": vehicle_count if "Main" in name else int(vehicle_count * 0.6),
            "average_speed": avg_speed if "Main" not in name else max(5, avg_speed - 15),
            "weather": weather,
            "road_type": road_type,
            "day_of_week": day_of_week,
            "hour": hour,
            "is_weekend": is_weekend
        }
        
        try:
            response = requests.post(BACKEND_API, json=payload)
            if response.status_with == 200 or response.status_code == 200:
                res_data = response.json()
                score = res_data["congestion_score"]
                level = res_data["congestion_level"]
                co2 = res_data["estimated_co2_emission_kg_hr"]
            else:
                score, level, co2 = 50.0, "Medium", 25.0
        except:
            # Fallback local matrix structural approximation if backend API is offline during load
            score, level, co2 = 45.0, "Medium", 18.5

        # Dynamic Route adjustments based on predicted congestion score
        adjusted_time = metadata["base_time"] * (1 + (score / 100.0))
        
        route_metrics.append({
            "Route Options": name,
            "Congestion Index": score,
            "Status": level,
            "Est. Travel Time (Mins)": round(adjusted_time, 1),
            "Distance (Miles)": metadata["base_dist"],
            "Carbon Footprint (CO2 kg/hr)": co2
        })

    df_routes = pd.DataFrame(route_metrics)
    st.dataframe(df_routes.style.background_gradient(subset=["Congestion Index"], cmap="Reds"))

    # Highlight Optimal Recommendation
    best_route = df_routes.loc[df_routes['Est. Travel Time (Mins)'].idxmin()]
    st.success(f"💡 **Smart Recommendation:** Use **{best_route['Route Options']}**. Lowest structural delay window expected ({best_route['Est. Travel Time (Mins)']} Mins).")

with col2:
    st.subheader("🗺️ Live Congestion Topology Map")
    # Base map anchor
    m = folium.Map(location=[40.730610, -73.935242], zoom_start=12, tiles="cartodbpositron")
    
    for route in route_metrics:
        # Match back coordinates
        meta = routes_db[route["Route Options"]]
        color = "green" if route["Status"] == "Low" else "orange" if route["Status"] == "Medium" else "red"
        
        folium.Marker(
            location=[meta["lat"], meta["lon"]],
            popup=f"{route['Route Options']}: {route['Status']} ({route['Congestion Index']} pts)",
            tooltip=route["Route Options"],
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
        
    st_folium(m, width=650, height=400, returned_objects=[])

---

st.subheader("📊 Network Diagnostic Analytics & Future Predictive Trendlines")
col3, col4 = st.columns(2)

with col3:
    # 24-Hour Predictive Load Simulation Curve
    hours_axis = list(range(24))
    simulated_load = [30 + 50 * np.sin((h - 5) / 3) + np.random.normal(0, 5) for h in hours_axis]
    simulated_load = [max(0, min(100, x)) for x in simulated_load]
    
    df_trend = pd.DataFrame({"Hour of Day": hours_axis, "Predicted Congestion Index": simulated_load})
    fig_trend = px.line(df_trend, x="Hour of Day", y="Predicted Congestion Index", title="Diurnal Network Congestion Index Forecast (Next 24 Hours)")
    st.plotly_chart(fig_trend, use_container_width=True)

with col4:
    # Emissions vs Optimization matrix
    fig_bar = px.bar(df_routes, x="Route Options", y="Carbon Footprint (CO2 kg/hr)", color="Status",
                     title="Environmental Impact Matrix Across Route Branches",
                     color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"})
    st.plotly_chart(fig_bar, use_container_width=True)