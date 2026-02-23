from fastapi import FastAPI, HTTPException
from controllers.deadline_controller import get_all_overdue_deadlines
from controllers.client_controller import get_all_clients_combined
import os

app = FastAPI()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Serveur CADS opérationnel"}

@app.get("/api/alerts")
def get_alerts():
    try:
        # On réutilise ta logique existante !
        data = get_all_overdue_deadlines()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients")
def get_clients():
    try:
        return get_all_clients_combined()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))