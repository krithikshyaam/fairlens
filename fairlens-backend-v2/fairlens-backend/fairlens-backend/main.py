"""
main.py
FairLens FastAPI backend entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import analyze, mitigate, report

load_dotenv()

app = FastAPI(
    title="FairLens API",
    description=(
        "AI-powered bias detection and mitigation platform. "
        "Upload any dataset or model to get a full fairness audit, "
        "SHAP explanations, mitigation options, and a compliance-ready PDF report."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allow React dev server) ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(analyze.router)
app.include_router(mitigate.router)
app.include_router(report.router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "FairLens API", "version": "1.0.0"}


@app.get("/", tags=["System"])
def root():
    return {
        "message": "FairLens API is running",
        "docs": "/docs",
        "endpoints": {
            "analyze":  "POST /analyze  — upload dataset, get bias analysis",
            "mitigate": "POST /mitigate — apply mitigation strategy",
            "report":   "POST /report   — download PDF audit report",
        }
    }
