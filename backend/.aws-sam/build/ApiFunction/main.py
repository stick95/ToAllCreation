from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI(title="ToAllCreation API", version="0.1.0")

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "ToAllCreation API - Hello World!",
        "version": "0.1.0",
        "status": "operational"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/hello")
def hello():
    return {
        "message": "Hello from the backend!",
        "timestamp": "2025-11-03",
        "service": "ToAllCreation Backend API"
    }

# Lambda handler
handler = Mangum(app)
