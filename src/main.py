from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import merchants_1o1
from src.api.middleware.validation import log_request_body
from src.utils.config import Config
import uvicorn
import multiprocessing

# Load config
config = Config()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"]:
        await log_request_body(request)
    response = await call_next(request)
    return response

# Include routers
app.include_router(merchants_1o1.router)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "config": {
            "fileverse_url": config.fileverse_api_url,
            "debug_mode": config.debug_mode,
            "game_rounds": config.game_rounds,
            "workers": multiprocessing.cpu_count()
        }
    }

if __name__ == "__main__":
    # Use multiple workers for better performance
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    ) 