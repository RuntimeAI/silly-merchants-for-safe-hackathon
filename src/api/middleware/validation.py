from fastapi import Request
import logging

logger = logging.getLogger(__name__)

async def log_request_body(request: Request):
    """Log request body for debugging"""
    try:
        body = await request.json()
        logger.info(f"Request body: {body}")
    except Exception as e:
        logger.error(f"Error reading request body: {str(e)}") 