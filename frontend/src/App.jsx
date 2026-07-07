import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import {
  Activity,
  Map as MapIcon,
  Navigation,
  BarChart2,
  Settings as SettingsIcon,
  Sun,
  Moon,
  UploadCloud,
  AlertTriangle,
  TrendingUp,
  Plus,
  RefreshCw,
  Play,
  Square,
  Home as HomeIcon,
  Database,
  Leaf,
  Clock,
  Compass,
  CheckCircle,
  Cpu
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

// Fix Leaflet marker icons bundling issues
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const BACKEND_URL = "http://localhost:8001/api";

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [theme, setTheme] = useState('dark');
  const [dbStats, setDbStats] = useState(null);
  const [modelCompare, setModelCompare] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationInterval, setSimulationInterval] = useState(null);
  const [notification, setNotification] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Sync theme attribute with DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Fetch initial analytical data
  const fetchData = async () => {
    try {
      const statsRes = await fetch(`${BACKEND_URL}/analytics/dashboard`);
      const statsData = await statsRes.json();
      setDbStats(statsData);

      const modelsRes = await fetch(`${BACKEND_URL}/predict/compare`);
      const modelsData = await modelsRes.json();
      setModelCompare(modelsData);
      
      const active = modelsData.find(m => m.is_active);
      setActiveModel(active ? active.name : 'None');
    } catch (err) {
      console.error("Failed to load dashboard statistics:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Show a status notification
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification(null);
    }, 4500);
  };

  // Real-time Traffic Simulator loop
  const toggleSimulation = async () => {
    if (isSimulating) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
      setIsSimulating(false);
      showNotification("Real-time simulation stopped.", "info");
    } else {
      setIsSimulating(true);
      showNotification("Real-time simulation activated. Streaming updates every 5 seconds...", "success");
      
      const intervalId = setInterval(async () => {
        try {
          const res = await fetch(`${BACKEND_URL}/traffic/simulate`, { method: 'POST' });
          const data = await res.json();
          fetchData(); // reload charts
        } catch (err) {
          console.error("Simulation tick failed:", err);
        }
      }, 5000);
      setSimulationInterval(intervalId);
    }
  };

  // Trigger retraining of all models
  const handleRetrain = async () => {
    setIsLoading(true);
    showNotification("Retraining ML pipeline. Processing outliers and fitting RF, XGBoost, GB, LSTM...", "info");
    try {
      const res = await fetch(`${BACKEND_URL}/models/train`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        showNotification("ML Models Retrained successfully! Active model updated.", "success");
        fetchData();
      } else {
        showNotification("ML model retraining failed. Check backend logs.", "error");
      }
    } catch (err) {
      showNotification("Network error triggering retraining pipeline.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  // Change active prediction model
  const selectActiveModel = async (name) => {
    try {
      const res = await fetch(`${BACKEND_URL}/models/select?name=${encodeURIComponent(name)}`, { method: 'POST' });
      if (res.ok) {
        showNotification(`Activated ${name} as predictive model.`, "success");
        fetchData();
      }
    } catch (err) {
      showNotification("Failed to swap active model.", "error");
    }
  };

  // Clear database rows
  const handleClearDb = async () => {
    if (window.confirm("Are you sure you want to clear all traffic data records from the database?")) {
      try {
        const res = await fetch(`${BACKEND_URL}/traffic/clear`, { method: 'POST' });
        if (res.ok) {
          showNotification("Cleared all database traffic records.", "info");
          fetchData();
        }
      } catch (err) {
        showNotification("Database wipe failed.", "error");
      }
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">🚦</div>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>TRAFFIC ENG</h2>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Smart Route Advisor</p>
          </div>
        </div>

        <nav className="nav-links">
          <li className={`nav-item ${activeTab === 'home' ? 'active' : ''}`} onClick={() => setActiveTab('home')}>
            <HomeIcon size={18} /> Home
          </li>
          <li className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <Activity size={18} /> Dashboard
          </li>
          <li className={`nav-item ${activeTab === 'predict' ? 'active' : ''}`} onClick={() => setActiveTab('predict')}>
            <Cpu size={18} /> Predictor Engine
          </li>
          <li className={`nav-item ${activeTab === 'routes' ? 'active' : ''}`} onClick={() => setActiveTab('routes')}>
            <Navigation size={18} /> Route Advisor
          </li>
          <li className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>
            <BarChart2 size={18} /> Visual Analytics
          </li>
          <li className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <SettingsIcon size={18} /> System Settings
          </li>
        </nav>

        <div className="sidebar-footer">
          <button className={`btn ${isSimulating ? 'btn-danger' : 'btn-secondary'}`} onClick={toggleSimulation} style={{ width: '100%' }}>
            {isSimulating ? <Square size={16} /> : <Play size={16} />}
            {isSimulating ? "Stop Simulator" : "Simulate Live"}
          </button>
          
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Database Mode: <span style={{ color: 'var(--color-low)', fontWeight: 700 }}>Dual Active</span>
          </div>
        </div>
      </aside>

      {/* Main Workspace Frame */}
      <main className="main-content">
        {/* Top bar header */}
        <header className="top-header">
          <div className="header-title-section">
            <h1>Traffic Congestion Advisor</h1>
            <p>Hackathon MVP Platform for Smart Commuting & Urban Analytics</p>
          </div>

          <div className="header-controls">
            {notification && (
              <div className={`alert-item alert-${notification.type}`} style={{ padding: '0.5rem 1rem', margin: 0, fontSize: '0.8rem' }}>
                {notification.message}
              </div>
            )}

            <div className="action-btn" style={{ width: 'auto', padding: '0 1rem', display: 'flex', gap: '0.5rem', fontSize: '0.85rem' }}>
              <Cpu size={16} /> Model: <strong style={{ color: '#a855f7' }}>{activeModel || 'None'}</strong>
            </div>

            <button className="theme-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>
        </header>

        {/* Tab Selection Layouts */}
        {activeTab === 'home' && <HomeView dbStats={dbStats} modelCompare={modelCompare} handleRetrain={handleRetrain} isLoading={isLoading} setActiveTab={setActiveTab} />}
        {activeTab === 'dashboard' && <DashboardView dbStats={dbStats} />}
        {activeTab === 'predict' && <PredictionView modelCompare={modelCompare} activeModel={activeModel} />}
        {activeTab === 'routes' && <RouteAdvisorView />}
        {activeTab === 'analytics' && <AnalyticsView dbStats={dbStats} />}
        {activeTab === 'settings' && (
          <SettingsView
            modelCompare={modelCompare}
            activeModel={activeModel}
            selectActiveModel={selectActiveModel}
            handleRetrain={handleRetrain}
            handleClearDb={handleClearDb}
            fetchData={fetchData}
            isLoading={isLoading}
          />
        )}
      </main>
    </div>
  );
}

// ==================== VIEW 1: HOME VIEW ====================
function HomeView({ dbStats, modelCompare, handleRetrain, isLoading, setActiveTab }) {
  const activeModelInfo = modelCompare.find(m => m.is_active);
  const totalModels = modelCompare.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Welcome Showcase Banner */}
      <section className="card" style={{ background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%)', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
        <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontFamily: 'var(--font-heading)' }}>Empowering Commuters and Planners</h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '800px', lineHeight: '1.6', marginBottom: '1.25rem' }}>
          This AI platform leverages machine learning architectures (including Gradient Boosting and LSTM time-series forecast models) to predict route delays, evaluate environmental impacts, and optimize commutes dynamically.
        </p>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn" onClick={() => setActiveTab('routes')}>
            <Navigation size={16} /> Open Route Advisor
          </button>
          <button className="btn btn-secondary" onClick={() => setActiveTab('dashboard')}>
            <Activity size={16} /> Go to Dashboard
          </button>
        </div>
      </section>

      {/* Main KPI metrics grid */}
      <section className="stats-grid">
        <div className="card stat-card">
          <div className="stat-header">
            <span>TRAFFIC ENTRIES</span>
            <div className="stat-icon"><Database size={16} /></div>
          </div>
          <div className="stat-value">{dbStats?.total_records ?? 0}</div>
          <div className="stat-desc">Historical & simulated entries logged</div>
        </div>

        <div className="card stat-card">
          <div className="stat-header">
            <span>AVG NETWORK CONGESTION</span>
            <div className="stat-icon"><Activity size={16} /></div>
          </div>
          <div className="stat-value">{dbStats?.avg_congestion ? `${dbStats.avg_congestion}%` : '0%'}</div>
          <div className="stat-desc">Aggregated road congestion level</div>
        </div>

        <div className="card stat-card">
          <div className="stat-header">
            <span>ACTIVE ALGORITHMS</span>
            <div className="stat-icon"><Cpu size={16} /></div>
          </div>
          <div className="stat-value">{totalModels}</div>
          <div className="stat-desc">RF, XGBoost, Gradient Boosting, LSTM</div>
        </div>

        <div className="card stat-card">
          <div className="stat-header">
            <span>ACTIVE ACCURACY</span>
            <div className="stat-icon"><CheckCircle size={16} /></div>
          </div>
          <div className="stat-value">{activeModelInfo?.accuracy ? `${(activeModelInfo.accuracy * 100).toFixed(1)}%` : 'N/A'}</div>
          <div className="stat-desc">Best model classification accuracy</div>
        </div>
      </section>

      <div className="card-grid-3">
        {/* Smart Advisor Summary / Alerts */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title"><AlertTriangle size={18} color="var(--color-medium)" /> Smart Routing Insights</h3>
          </div>
          <div className="alert-container">
            {dbStats?.active_alerts && dbStats.active_alerts.length > 0 ? (
              dbStats.active_alerts.map((alert, idx) => (
                <div key={idx} className={`alert-item ${alert.includes('🔴') ? 'alert-danger' : alert.includes('🟡') ? 'alert-warning' : ''}`}>
                  {alert}
                </div>
              ))
            ) : (
              <div className="alert-item">🟢 System loading: Initialize databases or trigger simulation updates in Settings.</div>
            )}
          </div>
        </div>

        {/* Current Active Predictor Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="card-header">
              <h3 className="card-title"><Cpu size={18} /> Active Model</h3>
            </div>
            <p style={{ fontSize: '1.25rem', fontWeight: 800, color: '#a855f7', marginBottom: '0.5rem' }}>
              {activeModelInfo?.name || "No Model Set"}
            </p>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <div>RMSE: <strong>{activeModelInfo?.rmse ?? 'N/A'}</strong></div>
              <div>MAE: <strong>{activeModelInfo?.mae ?? 'N/A'}</strong></div>
              <div>R² Score: <strong>{activeModelInfo?.r2_score ?? 'N/A'}</strong></div>
            </div>
          </div>

          <button className="btn btn-secondary" onClick={handleRetrain} disabled={isLoading} style={{ marginTop: '1.5rem', width: '100%' }}>
            <RefreshCw size={14} className={isLoading ? "spin-animation" : ""} /> {isLoading ? "Retraining..." : "Retrain Pipeline"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ==================== VIEW 2: DASHBOARD VIEW ====================
function DashboardView({ dbStats }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  // Initialize and update the Leaflet map
  useEffect(() => {
    if (mapRef.current && !mapInstanceRef.current) {
      // Create map anchor centered in NYC (matching base datasets coordinates)
      mapInstanceRef.current = L.map(mapRef.current).setView([40.730610, -73.935242], 12);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      }).addTo(mapInstanceRef.current);
    }

    const fetchMarkers = async () => {
      if (mapInstanceRef.current) {
        // Clear old markers before drawing new ones
        mapInstanceRef.current.eachLayer((layer) => {
          if (layer instanceof L.Marker) {
            mapInstanceRef.current.removeLayer(layer);
          }
        });

        try {
          const res = await fetch(`${BACKEND_URL}/traffic/data?limit=40`);
          const entries = await res.json();
          
          entries.forEach(entry => {
            const color = entry.congestion_level === 'High' ? 'red' : entry.congestion_level === 'Medium' ? 'orange' : 'green';
            
            // Custom colored SVG pin marker
            const customIcon = L.divIcon({
              html: `<span style="background-color: ${color}; width: 14px; height: 14px; border: 2px solid white; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.5)"></span>`,
              className: 'custom-map-pin',
              iconSize: [14, 14]
            });

            L.marker([entry.latitude, entry.longitude], { icon: customIcon })
              .addTo(mapInstanceRef.current)
              .bindPopup(`
                <div style="color: #111; font-family: sans-serif; font-size: 0.85rem">
                  <strong>Junction node:</strong> ${entry.road_type}<br/>
                  Congestion Score: <strong>${entry.congestion_score.toFixed(1)}</strong> (${entry.congestion_level})<br/>
                  Speed: ${entry.average_speed} mph<br/>
                  Volume: ${entry.vehicle_count} vehicles
                </div>
              `);
          });
        } catch (err) {
          console.error("Map markers sync fail:", err);
        }
      }
    };

    fetchMarkers();
  }, [dbStats]);

  return (
    <div className="card-grid-3">
      {/* Left Column: Map */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div className="card-header" style={{ marginBottom: 0 }}>
          <h3 className="card-title"><MapIcon size={18} /> Localized Live Bottlenecks Map</h3>
        </div>
        <div className="map-container-wrapper">
          <div ref={mapRef} style={{ width: '100%', height: '100%' }}></div>
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '0 0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'green' }}></span> Low Congestion (&lt;35)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'orange' }}></span> Medium (35-70)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'red' }}></span> High (&gt;70)
          </div>
        </div>
      </div>

      {/* Right Column: Mini analytics summary */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="card" style={{ flexGrow: 1 }}>
          <div className="card-header">
            <h3 className="card-title"><AlertTriangle size={18} /> Real-Time Alerts</h3>
          </div>
          <div className="alert-container">
            {dbStats?.active_alerts?.map((alert, idx) => (
              <div key={idx} className={`alert-item ${alert.includes('🔴') ? 'alert-danger' : alert.includes('🟢') ? 'alert-success' : 'alert-warning'}`} style={{ fontSize: '0.85rem' }}>
                {alert}
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>System Diagnostics</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
              <span>Database Sync</span>
              <strong style={{ color: 'var(--color-low)' }}>ONLINE</strong>
            </div>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
              <span>Streaming updates</span>
              <strong>5s Interval</strong>
            </div>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between' }}>
              <span>Sample coordinates</span>
              <span>40.7128, -74.0060</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== VIEW 3: PREDICTION VIEW ====================
function PredictionView({ modelCompare, activeModel }) {
  const [vehicleCount, setVehicleCount] = useState(85);
  const [avgSpeed, setAvgSpeed] = useState(42);
  const [weather, setWeather] = useState('Clear');
  const [roadType, setRoadType] = useState('Arterial');
  const [hour, setHour] = useState(new Date().getHours());
  const [selectedModel, setSelectedModel] = useState(activeModel || '');
  const [prediction, setPrediction] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);

  // Sync selected model name
  useEffect(() => {
    if (activeModel) {
      setSelectedModel(activeModel);
    }
  }, [activeModel]);

  const handlePredict = async (e) => {
    e.preventDefault();
    setIsPredicting(true);
    
    const now = new Date();
    const dayOfWeek = now.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6 ? 1 : 0;

    const payload = {
      latitude: 40.7128, // base coordinate anchor
      longitude: -74.0060,
      vehicle_count: parseInt(vehicleCount),
      average_speed: parseFloat(avgSpeed),
      weather: weather,
      road_type: roadType,
      hour: parseInt(hour),
      day_of_week: dayOfWeek,
      is_weekend: isWeekend,
      is_holiday: false,
      model_name: selectedModel || null
    };

    try {
      const res = await fetch(`${BACKEND_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const data = await res.json();
        setPrediction(data);
      }
    } catch (err) {
      console.error("Single prediction failed:", err);
    } finally {
      setIsPredicting(false);
    }
  };

  const levelColor = prediction?.congestion_level === 'High' ? 'var(--color-high)' : prediction?.congestion_level === 'Medium' ? 'var(--color-medium)' : 'var(--color-low)';

  return (
    <div className="card-grid-3">
      {/* Left Column: Form */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title"><Cpu size={18} /> Forecast Parameters</h3>
        </div>
        <form onSubmit={handlePredict}>
          <div className="form-group">
            <label>Prediction Algorithm</label>
            <select className="form-control" value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
              {modelCompare.map(m => (
                <option key={m.name} value={m.name}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Weather Condition</label>
              <select className="form-control" value={weather} onChange={(e) => setWeather(e.target.value)}>
                <option value="Clear">Clear</option>
                <option value="Rainy">Rainy</option>
                <option value="Snowy">Snowy</option>
              </select>
            </div>

            <div className="form-group">
              <label>Road Class</label>
              <select className="form-control" value={roadType} onChange={(e) => setRoadType(e.target.value)}>
                <option value="Highway">Highway</option>
                <option value="Arterial">Arterial</option>
                <option value="Local">Local</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label>Observed Vehicle Count: <strong>{vehicleCount}</strong></label>
            </div>
            <input type="range" min="5" max="300" step="5" value={vehicleCount} onChange={(e) => setVehicleCount(e.target.value)} style={{ width: '100%', cursor: 'pointer' }} />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label>Average Vehicle Speed: <strong>{avgSpeed} mph</strong></label>
            </div>
            <input type="range" min="5" max="80" step="1" value={avgSpeed} onChange={(e) => setAvgSpeed(e.target.value)} style={{ width: '100%', cursor: 'pointer' }} />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label>Forecast Time Window (Hour): <strong>{hour}:00</strong></label>
            </div>
            <input type="range" min="0" max="23" value={hour} onChange={(e) => setHour(e.target.value)} style={{ width: '100%', cursor: 'pointer' }} />
          </div>

          <button className="btn" type="submit" disabled={isPredicting} style={{ width: '100%', marginTop: '1rem' }}>
            {isPredicting ? "Computing..." : "Run Forecast Engine"}
          </button>
        </form>
      </div>

      {/* Right Column: Prediction Outcomes */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', minHeight: '350px' }}>
        {prediction ? (
          <div style={{ width: '100%' }}>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Prediction Results</h3>
            
            {/* Congestion score progress bar */}
            <div style={{ position: 'relative', width: '160px', height: '160px', margin: '0 auto 1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: `8px solid ${levelColor}`, borderRadius: '50%', boxShadow: '0 0 20px rgba(0,0,0,0.1)' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 800 }}>{prediction.congestion_score.toFixed(0)}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Score</span>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Predicted Congestion Level</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: levelColor }}>
                {prediction.congestion_level}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem', fontSize: '0.85rem' }}>
              <div style={{ borderRight: '1px solid var(--border-color)' }}>
                <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.2rem' }}>
                  <Leaf size={14} color="#10b981" /> Carbon Footprint
                </div>
                <strong style={{ fontSize: '1.1rem' }}>{prediction.co2_emissions.toFixed(1)} kg/hr</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-secondary)' }}>Model Used</div>
                <strong style={{ fontSize: '1.1rem' }}>{prediction.model_used}</strong>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)' }}>
            <Cpu size={48} style={{ marginBottom: '1rem', strokeWidth: 1.2 }} />
            <p>Set parameters and click <strong>Run Forecast Engine</strong> to calculate bottlenecks.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== VIEW 4: ROUTE ADVISOR VIEW ====================
function RouteAdvisorView() {
  const [weather, setWeather] = useState('Clear');
  const [vehicleCount, setVehicleCount] = useState(85);
  const [avgSpeed, setAvgSpeed] = useState(42);
  const [routesData, setRoutesData] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [recommendation, setRecommendation] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const activePolylineRef = useRef(null);

  // Initialize Route Advisor Map
  useEffect(() => {
    if (mapRef.current && !mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current).setView([40.730610, -73.935242], 12);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap'
      }).addTo(mapInstanceRef.current);
    }
  }, []);

  const handleAdvisorSearch = async (e) => {
    if (e) e.preventDefault();
    setIsSearching(true);

    const payload = {
      start_lat: 40.7128,
      start_lon: -74.0060,
      end_lat: 40.7484,
      end_lon: -73.9857,
      vehicle_count: parseInt(vehicleCount),
      average_speed: parseFloat(avgSpeed),
      weather: weather,
      road_type: "Highway"
    };

    try {
      const res = await fetch(`${BACKEND_URL}/routes/advisor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setRoutesData(data.routes);
        setRecommendation(data.recommendation);
        
        // Auto select the fastest option
        const fastest = data.routes.find(r => r.is_fastest);
        if (fastest) {
          drawRouteOnMap(fastest);
        }
      }
    } catch (err) {
      console.error("Advisor calculation error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  // Perform initial search automatically on load
  useEffect(() => {
    handleAdvisorSearch();
  }, []);

  const drawRouteOnMap = (route) => {
    setSelectedRoute(route.name);
    
    if (mapInstanceRef.current) {
      // Remove previous polyline
      if (activePolylineRef.current) {
        mapInstanceRef.current.removeLayer(activePolylineRef.current);
      }

      // Remove previous markers
      mapInstanceRef.current.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
          mapInstanceRef.current.removeLayer(layer);
        }
      });

      const coords = route.waypoints;
      const color = route.predicted_level === 'High' ? '#ef4444' : route.predicted_level === 'Medium' ? '#f59e0b' : '#10b981';

      // Draw polyline route
      activePolylineRef.current = L.polyline(coords, {
        color: color,
        weight: 6,
        opacity: 0.8,
        lineCap: 'round'
      }).addTo(mapInstanceRef.current);

      // Fit map window bounds to coordinates
      mapInstanceRef.current.fitBounds(activePolylineRef.current.getBounds(), { padding: [30, 30] });

      // Add Start Marker
      L.marker(coords[0])
        .addTo(mapInstanceRef.current)
        .bindPopup("Start Location: Downtown Hub");

      // Add End Marker
      L.marker(coords[coords.length - 1])
        .addTo(mapInstanceRef.current)
        .bindPopup("Destination: Tech Corridor Ext");
    }
  };

  return (
    <div className="card-grid-3">
      {/* Left Column: Search & Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Parameters input */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}><Compass size={18} /> Commute Parameters</h3>
          <form onSubmit={handleAdvisorSearch}>
            <div className="form-group">
              <label>Current Weather</label>
              <select className="form-control" value={weather} onChange={(e) => setWeather(e.target.value)}>
                <option value="Clear">Clear</option>
                <option value="Rainy">Rainy</option>
                <option value="Snowy">Snowy</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Observed Vehicle count: <strong>{vehicleCount}</strong></label>
              <input type="range" min="5" max="300" step="5" value={vehicleCount} onChange={(e) => setVehicleCount(e.target.value)} style={{ width: '100%', cursor: 'pointer' }} />
            </div>

            <div className="form-group">
              <label>Average Velocity (mph): <strong>{avgSpeed}</strong></label>
              <input type="range" min="5" max="80" step="1" value={avgSpeed} onChange={(e) => setAvgSpeed(e.target.value)} style={{ width: '100%', cursor: 'pointer' }} />
            </div>

            <button className="btn" type="submit" disabled={isSearching} style={{ width: '100%' }}>
              {isSearching ? "Calculating..." : "Find Best Routes"}
            </button>
          </form>
        </div>

        {/* Advisor recommendations cards */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}><Navigation size={18} /> Route Options</h3>
          
          <div className="route-advisor-panel">
            {routesData.map(route => {
              const borderThemeColor = route.predicted_level === 'High' ? 'var(--color-high)' : route.predicted_level === 'Medium' ? 'var(--color-medium)' : 'var(--color-low)';
              
              return (
                <div
                  key={route.name}
                  className={`route-card ${selectedRoute === route.name ? 'selected' : ''}`}
                  onClick={() => drawRouteOnMap(route)}
                >
                  <div className="route-card-header">
                    <span className="route-card-title">{route.name.split(' (')[0]}</span>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      {route.is_fastest && <span className="badge-route-tag">FASTEST</span>}
                      {route.is_least_congested && <span className="badge-route-tag tag-green">GREENEST</span>}
                    </div>
                  </div>

                  <div className="route-metrics-row">
                    <div className="route-metric">
                      Time: <span style={{ color: borderThemeColor }}>{route.adjusted_time} mins</span>
                    </div>
                    <div className="route-metric">
                      Distance: <span>{route.distance} mi</span>
                    </div>
                    <div className="route-metric">
                      CO2: <span>{route.co2_emissions} kg</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Column: Leaflet map visual */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {recommendation && (
          <div className="alert-item alert-success" style={{ fontSize: '0.85rem' }}>
            {recommendation}
          </div>
        )}
        <div className="map-container-wrapper" style={{ height: '530px' }}>
          <div ref={mapRef} style={{ width: '100%', height: '100%' }}></div>
        </div>
      </div>
    </div>
  );
}

// ==================== VIEW 5: ANALYTICS VIEW ====================
function AnalyticsView({ dbStats }) {
  if (!dbStats || dbStats.total_records === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <BarChart2 size={48} style={{ strokeWidth: 1.2, color: 'var(--text-muted)', marginBottom: '1rem' }} />
        <p>No analytics data logged. Upload a dataset or run the simulation generator first.</p>
      </div>
    );
  }

  // Pre-process 24h trends trendline graph
  const trendData = dbStats.hourly_trends.map(t => ({
    Hour: `${t.hour}:00`,
    "Congestion Score": parseFloat(t.avg_score.toFixed(1))
  }));

  // Weather impacts chart
  const weatherData = dbStats.weather_impact.map(w => ({
    Weather: w.weather,
    "Congestion Score": parseFloat(w.avg_score.toFixed(1)),
    "Avg Velocity (mph)": parseFloat(w.avg_speed.toFixed(1))
  }));

  // Road impacts chart
  const roadData = dbStats.road_impact.map(r => ({
    "Road Type": r.road_type,
    "Congestion Score": parseFloat(r.avg_score.toFixed(1)),
    "Avg Velocity (mph)": parseFloat(r.avg_speed.toFixed(1))
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div className="card-grid">
        {/* Chart 1: Diurnal 24 Hour load curves */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}><TrendingUp size={16} /> Diurnal Network Congestion Index Forecast (24 Hours)</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCong" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="Hour" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--bg-sidebar)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }} />
                <Area type="monotone" dataKey="Congestion Score" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorCong)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Weather Impact */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}><Activity size={16} /> Weather Congestion Modifiers</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={weatherData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="Weather" tick={{ fill: 'var(--text-secondary)' }} />
                <YAxis tick={{ fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--bg-sidebar)', borderColor: 'var(--border-color)' }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="Congestion Score" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Avg Velocity (mph)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Chart 3: Road Class impact */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}><BarChart2 size={16} /> Performance Metrics Across Road Classifications</h3>
        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={roadData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="Road Type" tick={{ fill: 'var(--text-secondary)' }} />
              <YAxis tick={{ fill: 'var(--text-secondary)' }} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-sidebar)', borderColor: 'var(--border-color)' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Congestion Score" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Avg Velocity (mph)" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ==================== VIEW 6: SETTINGS VIEW ====================
function SettingsView({ modelCompare, activeModel, selectActiveModel, handleRetrain, handleClearDb, fetchData, isLoading }) {
  const fileInputRef = useRef(null);

  const handleCsvUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/traffic/upload`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        alert("CSV Dataset uploaded and processed successfully!");
        fetchData(); // reload
      } else {
        const errData = await res.json();
        alert(`CSV Upload Failed: ${errData.detail}`);
      }
    } catch (err) {
      alert("Network error occurred during CSV upload.");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Algorithms Comparison block */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1.25rem' }}><Cpu size={18} /> Model Performance Comparison Matrix</h3>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Model Architecture</th>
                <th>Classification Accuracy</th>
                <th>F1 Macro Score</th>
                <th>RMSE (Lower is Better)</th>
                <th>MAE</th>
                <th>R² Score</th>
                <th>Current Status</th>
              </tr>
            </thead>
            <tbody>
              {modelCompare.map(model => (
                <tr key={model.name}>
                  <td style={{ fontWeight: 600 }}>{model.name}</td>
                  <td>{model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : 'N/A'}</td>
                  <td>{model.f1_score ? model.f1_score.toFixed(3) : 'N/A'}</td>
                  <td>{model.rmse ? model.rmse.toFixed(3) : 'N/A'}</td>
                  <td>{model.mae ? model.mae.toFixed(3) : 'N/A'}</td>
                  <td>{model.r2_score ? model.r2_score.toFixed(3) : 'N/A'}</td>
                  <td>
                    {model.is_active ? (
                      <span className="badge badge-low">Active Predictor</span>
                    ) : (
                      <button className="btn btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', borderRadius: '5px' }} onClick={() => selectActiveModel(model.name)}>
                        Activate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card-grid">
        {/* CSV Upload Section */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 className="card-title"><UploadCloud size={18} /> CSV Traffic Dataset Ingestion</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            Upload bulk traffic csv coordinates. Re-train models instantly on newly ingested records. Required fields:
            <code> timestamp, vehicle_count, average_speed, weather, road_type, latitude, longitude</code>.
          </p>
          
          <div className="file-upload-zone" onClick={() => fileInputRef.current.click()}>
            <UploadCloud className="file-upload-icon" />
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.25rem' }}>Select CSV File to Upload</h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Only CSV files supported</p>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleCsvUpload}
              className="file-input-hidden"
              accept=".csv"
            />
          </div>
        </div>

        {/* System Administration controls */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifySelf: 'stretch', justifyContent: 'space-between' }}>
          <div>
            <h3 className="card-title" style={{ marginBottom: '1rem' }}><SettingsIcon size={18} /> Database & ML Management</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '1.25rem' }}>
              Administer database cache states and trigger neural network training parameters. Training runs locally across RF, XGBoost, and LSTM estimators.
            </p>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <button className="btn" onClick={handleRetrain} disabled={isLoading} style={{ width: '100%' }}>
              <RefreshCw size={16} className={isLoading ? "spin-animation" : ""} /> {isLoading ? "Fitting estimators..." : "Retrain All ML Models"}
            </button>
            <button className="btn btn-secondary btn-danger" onClick={handleClearDb} style={{ width: '100%' }}>
              Clear Database Entries
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
