from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.telemetry import router as telemetry_router
from app.api.devices import router as devices_router
from app.api.usage import router as usage_router
from app.api.behavior import router as behavior_router
from app.api.alerts import router as alerts_router
from app.api.settings import router as settings_router
from app.api.reports import router as reports_router

app = FastAPI(
    title="Enterprise Wi-Fi Monitoring System",
    description="Vendor-independent enterprise Wi-Fi network monitoring platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
    "http://10.0.2.15:5173",
    "http://127.0.0.1:5173",
    "http://172.18.0.1:5173",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router)
app.include_router(telemetry_router)
app.include_router(usage_router)
app.include_router(behavior_router)
app.include_router(alerts_router)
app.include_router(settings_router)
app.include_router(reports_router)

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "application": "Enterprise Wi-Fi Monitoring System",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
