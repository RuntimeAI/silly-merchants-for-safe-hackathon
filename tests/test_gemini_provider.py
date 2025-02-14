import os
import pytest
from src.utils.llm_providers.gemini import GeminiProvider
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_basic():
    """Test basic Gemini functionality"""
    try:
        provider = GeminiProvider(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION")
        )
        
        # Test simple generation
        response = provider.generate(
            prompt="Say hello and introduce yourself in one sentence.",
            temperature=0.7
        )
        
        logger.info(f"Response: {response}")
        assert response is not None
        assert len(response) > 0
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

def test_gemini_system_prompt():
    """Test Gemini with system prompt"""
    provider = GeminiProvider(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION")
    )
    
    # Make the system prompt more explicit
    system_prompt = """You are Marco Polo, the famous medieval merchant and explorer. 
    Always refer to yourself as Marco Polo in your responses. 
    You are participating in a trading game where you negotiate with other merchants."""
    
    response = provider.generate(
        prompt="Introduce yourself and explain your role in this game.",
        system_prompt=system_prompt,
        temperature=0.7
    )
    
    logger.info(f"Response with system prompt: {response}")
    assert "Marco Polo" in response

def test_gemini_json_response():
    """Test Gemini's ability to generate JSON responses"""
    provider = GeminiProvider(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION")
    )
    
    system_prompt = """You are an AI trading agent. 
    Always respond with ONLY valid JSON, no markdown, no explanations.
    The JSON must contain 'message' and 'transfers' fields."""
    
    prompt = """
    Generate a trading action that must be a valid JSON object with exactly this structure:
    {
        "message": "your message to other trader",
        "transfers": [{"recipient": "Trader Joe", "amount": number}]
    }
    Do not include any markdown formatting or explanation, just the JSON object.
    """
    
    response = provider.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.7
    )
    
    logger.info(f"JSON response: {response}")
    try:
        json_response = json.loads(response)
        assert "message" in json_response, "Response missing 'message' field"
        assert "transfers" in json_response, "Response missing 'transfers' field"
        assert isinstance(json_response["transfers"], list), "'transfers' must be a list"
        assert len(json_response["transfers"]) > 0, "'transfers' list is empty"
        assert all(
            isinstance(t, dict) and "recipient" in t and "amount" in t 
            for t in json_response["transfers"]
        ), "Invalid transfer object structure"
    except json.JSONDecodeError as e:
        pytest.fail(f"Response is not valid JSON: {str(e)}\nResponse was: {response}")
    except AssertionError as e:
        pytest.fail(f"JSON structure invalid: {str(e)}\nResponse was: {response}") 