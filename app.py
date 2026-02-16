from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import traceback
from datetime import datetime
from main import *
from main import process_new_session, df_ctx

app = FastAPI()

def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if obj is pd.NaT:
        return None
    return obj

class SessionInput(BaseModel):
    user_id: int
    timestamp: str
    login_attempts: int
    failed_logins: int
    session_duration: float
    data_volume: float
    unusual_time_access: int
    ip_reputation_score: float
    browser_type: str

@app.get("/", response_class=HTMLResponse)
def dashboard():
    with open("static/dashboard.html") as f:
        return f.read()

@app.post("/evaluate-session")
def evaluate_session(session: SessionInput):
    try:
        df_new = pd.DataFrame([session.dict()])
        df_new["timestamp"] = pd.to_datetime(df_new["timestamp"], utc=True, errors="coerce")

        result = process_new_session(df_new, df_ctx)

        # force timestamp to ISO string if present
        if "timestamp" in result:
            result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True, errors="coerce").isoformat()

        return JSONResponse(content=make_json_safe(result))

    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{e}\n\n{tb}")