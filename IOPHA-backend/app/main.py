import logging

from fastapi import FastAPI

from app.logging import CentralizedLoggingMiddleware, JsonTelemetryFormatter

log_handler = logging.StreamHandler()
log_handler.setFormatter(JsonTelemetryFormatter())
logger = logging.getLogger("com.example.PatientService")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

app = FastAPI(title="IOPHA Backend API")
app.add_middleware(CentralizedLoggingMiddleware, logger=logger)


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}


@app.get("/directory")
def directory() -> dict:
    return {"physicians": []}


@app.post("/chat/message")
def chat_message() -> dict:
    return {"message": "Hello from IOPHA"}


@app.get("/patients/{patient_id}")
def get_patient(patient_id: int) -> dict:
    return {"patient_id": patient_id}
