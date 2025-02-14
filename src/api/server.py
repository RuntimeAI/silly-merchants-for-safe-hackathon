from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from .routers import merchants_1o1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('api_server.log')  # Log to file
    ]
)

logger = logging.getLogger("api_server")

app = FastAPI(
    title="Silly Merchants API",
    description="API for the Silly Merchants trading game",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(merchants_1o1.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Silly Merchants API server")

def run_server():
    """Run the FastAPI server"""
    logger.info("Initializing server")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server() 