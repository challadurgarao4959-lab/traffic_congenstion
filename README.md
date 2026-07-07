# Traffic Congestion Prediction & Smart Route Advisor

An AI-powered, end-to-end web application that predicts traffic congestion levels, forecasts bottleneck windows (15–60 minutes ahead), recommends energy-efficient alternative routes, and displays real-time urban traffic analytics on an interactive map.

---

## 🚀 Key Features

1. **Analytical Dashboard:** Interactive Leaflet maps rendering localized traffic points color-coded by congestion severity.
2. **Machine Learning Pipeline:** Trains and compares 4 architectures:
   * **XGBoost Regressor**
   * **Random Forest Regressor**
   * **Gradient Boosting Regressor**
   * **Custom NumPy-based LSTM** (Long Short-Term Memory Neural Network for time-series forecasting)
3. **Smart Route Advisor:** Recalculates travel times dynamically for Expressway, Secondary, and Local Bypasses, identifying the **Fastest** and **Greenest (Least Congested)** routes.
4. **Data Ingestion:** Manual inputs, real-time updates simulation, and drag-and-drop CSV dataset uploader with outlier detection filters.
5. **Aesthetics & Performance:** Sleek dark/light responsive layout using modern CSS, glassmorphism card items, and micro-animations.

---

## 🛠️ Project Architecture

* **Frontend:** React (Vite, Recharts, Leaflet Maps, Lucide Icons)
* **Backend:** FastAPI (Python 3.14 compatible, Pydantic data schemas, SQLAlchemy ORM)
* **Database:** Dual-mode support (SQLite for instant local testing, PostgreSQL-ready for production deployment)

---

## 📂 Directory Structure

```
traffic-congestion-predictor/
├── backend/
│   ├── database.py       # SQL Alchemy connection and dual-DB config
│   ├── models.py         # DB tables (TrafficEntry, MLModel, SavedRoute)
│   ├── schemas.py        # Pydantic schemas for request/response validation
│   ├── crud.py           # Database transaction operations
│   ├── ml_engine.py      # ML preprocessing and training pipeline
│   ├── main.py           # FastAPI entry point & startup processes
│   └── router.py         # API router endpoints
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Root dashboard layouts and page controllers
│   │   ├── index.css     # CSS variable system (Dark/Light mode)
│   │   └── main.jsx      # Vite entry point
│   ├── index.html        # Leaflet CDN assets and title metadata
│   └── package.json      # React dependencies
├── models/
│   ├── lstm_numpy.py     # Pure NumPy LSTM class with backprop & Adam optimizer
│   └── *.pkl             # Serialized model binaries (RF, XGBoost, etc.)
├── data/
│   └── synthetic_traffic_data.csv   # Local sample dataset
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## 💻 Installation & Getting Started

### 1. Backend Setup

1. Open a terminal and navigate to the project root directory.
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Upgrade pip and install all required python libraries:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **(Optional)** Configure PostgreSQL. If you want to use PostgreSQL, export the `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="postgresql://username:password@localhost:5432/dbname"
   ```
   *If unset, the backend automatically defaults to SQLite, creating `traffic_predictor.db` in the root folder.*
5. Run the FastAPI development server:
   ```bash
   python3 backend/main.py
   ```
   The backend will start on **`http://localhost:8000`**. You can view the interactive swagger API documentation at **`http://localhost:8000/docs`**.

---

### 2. Frontend Setup

1. Open a new terminal tab/window and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will start on **`http://localhost:5173`** (or another port outputted in the shell).

---

## 🔌 API Endpoints Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/traffic/data` | `GET` | Fetches historical and simulated traffic logs. |
| `/api/traffic/data` | `POST` | Logs a new traffic entry manually. |
| `/api/traffic/upload` | `POST` | Uploads a CSV dataset of traffic records. |
| `/api/traffic/simulate` | `POST` | Generates a live simulated data stream across major junctions. |
| `/api/predict` | `POST` | Predicts congestion score/level for a given coordinate & parameters. |
| `/api/predict/compare` | `GET` | Returns performance metrics for all ML models. |
| `/api/models/train` | `POST` | Re-runs preprocessing, fits all models, and registers the best model. |
| `/api/routes/advisor` | `POST` | Compares path choices and returns optimal route advisor decisions. |
| `/api/analytics/dashboard` | `GET` | Aggregates graphs metadata (weather, hourly trendlines, road type metrics). |

---

## 🧠 ML Preprocessing & Feature Engineering

When a raw CSV or request is received, the backend performs the following:
* **Missing Values Imputation:** Numerical features are filled with their column median.
* **Outlier Removal:** Rows where the numeric Z-score ($z = \frac{x-\mu}{\sigma}$) exceeds $\pm 3.0$ are pruned.
* **Peak Hour Indicator:** Maps hours to a binary flag ($1$ for 8-10 AM and 5-7 PM rush windows, else $0$).
* **Weekend Flag:** Detects if the day of the week is Saturday ($5$) or Sunday ($6$).
* **Z-score Standardization:** Features are scaled using the mean and variance computed on the training set.
* **Categorical Encoding:** One-hot encoding handles inputs for weather class (`Rainy`, `Snowy`) and road classes (`Highway`, `Local`).

---

## 🎓 Mathematical Modeling

### 1. LSTM Regressor Equations
Our custom pure-NumPy LSTM processes sequential time windows to forecast trends:
* **Gating calculations:**
  $$i_t = \sigma(W_i x_t + U_i h_{t-1} + b_i) \quad \text{(Input Gate)}$$
  $$f_t = \sigma(W_f x_t + U_f h_{t-1} + b_f) \quad \text{(Forget Gate)}$$
  $$o_t = \sigma(W_o x_t + U_o h_{t-1} + b_o) \quad \text{(Output Gate)}$$
  $$\tilde{c}_t = \tanh(W_c x_t + U_c h_{t-1} + b_c) \quad \text{(Candidate Cell State)}$$
* **State Updates:**
  $$c_t = f_t \odot c_{t-1} + i_t \odot \tilde{c}_t \quad \text{(Cell State)}$$
  $$h_t = o_t \odot \tanh(c_t) \quad \text{(Hidden State)}$$
* **Output Projection:**
  $$y_t = W_y h_t + b_y \quad \text{(Congestion Score)}$$

### 2. Smart Route Delay Adjustments
Congestion increases transit delays relative to the base travel time ($T_{\text{base}}$):
$$T_{\text{adjusted}} = T_{\text{base}} \times \left(1 + \frac{\text{Congestion Score}}{50.0}\right)$$
* At maximum congestion (Score = 100), travel speed slows down and travel duration increases by **3x** (e.g., a 12-minute commute becomes 36 minutes).
* At zero congestion (Score = 0), transit duration matches the base time.
* Carbon emissions are scaled by vehicle count and transit duration to optimize green commuter routing.
