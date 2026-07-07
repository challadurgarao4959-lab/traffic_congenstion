# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend import db_models as models, router, ml_engine, crud
from backend.database import engine, SessionLocal

# Initialize Database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Traffic Congestion & Smart Route Advisor Engine",
    description="FastAPI Backend for predicting congestion, suggesting green routes, and visualizing networks.",
    version="2.0"
)

# CORS Middleware Configuration (Essential for React connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins in local hackathon mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router.router, prefix="/api")

@app.on_event("startup")
def startup_event():
    """
    On startup, verify if models are trained and data is seeded.
    If not, perform seeding and model training automatically.
    """
    db = SessionLocal()
    try:
        # Check if traffic entries exist
        entry_count = db.query(models.TrafficEntry).count()
        if entry_count == 0:
            print("No traffic records found. Seeding database...")
            ml_engine.generate_and_seed_data(db, num_rows=1500)
            
        # Ensure default route geometries are created
        crud.get_routes(db)
        
        # Check if models are trained
        model_count = db.query(models.MLModel).count()
        active_model = crud.get_active_model(db)
        if model_count == 0 or not active_model:
            print("No trained ML models found. Running training pipeline...")
            ml_engine.train_and_evaluate_all(db)
            
        print("FastAPI Backend startup processes completed successfully.")
    except Exception as e:
        print(f"Error during backend startup processes: {str(e)}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Traffic Congestion & Smart Route Advisor API",
        "version": "2.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)