import asyncio
import logging
from src.utils.fileverse_client import FileverseClient
import json
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fileverse_upload():
    """Test uploading content to Fileverse"""
    client = FileverseClient()
    
    # Test data
    test_game_data = {
        "timestamp": "2025-02-15T10:30:00.000Z",
        "winner": "Test Player",
        "final_standings": {
            "Test Player": 12,
            "Bot Player": 8
        },
        "history": {
            "messages": [
                {
                    "round": 1,
                    "speaker": "Test Player",
                    "message": "Hello, this is a test message"
                },
                {
                    "round": 1,
                    "speaker": "Bot Player",
                    "message": "This is a test response"
                }
            ],
            "transfers": [
                {
                    "round": 1,
                    "sender": "Test Player",
                    "recipient": "Bot Player",
                    "amount": 2
                }
            ]
        }
    }
    
    try:
        # Test 1: Simple content upload
        logger.info("\nTest 1: Simple content upload")
        simple_content = "Hello Fileverse!"
        response = requests.post(
            f'{client.base_url}/api/files',
            headers={'Content-Type': 'application/json'},
            json={'content': simple_content}
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Upload response: {json.dumps(result, indent=2)}")
        
        # Test 2: Markdown formatting
        logger.info("\nTest 2: Markdown formatting")
        markdown = client._format_game_markdown("test-game-id", test_game_data)
        logger.info(f"Generated markdown:\n{markdown}")
        
        # Test 3: Game log upload
        logger.info("\nTest 3: Game log upload")
        file_id = await client.save_game_log("test-game-id", test_game_data)
        logger.info(f"Successfully uploaded file with ID: {file_id}")
        
        # Test 4: File retrieval
        logger.info("\nTest 4: File retrieval")
        retrieved = client.get_file(file_id)
        logger.info(f"Retrieved file response: {json.dumps(retrieved, indent=2)}")
        
        logger.info("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}")
        raise

async def test_fileverse_health():
    """Test Fileverse health endpoint"""
    client = FileverseClient()
    
    try:
        response = requests.get(f'{client.base_url}/health')
        response.raise_for_status()
        result = response.json()
        
        logger.info("\nHealth check response:")
        logger.info(json.dumps(result, indent=2))
        
        assert result.get('status') == 'ok', "Health check failed"
        logger.info("✅ Health check passed!")
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        raise

# Update main to run both tests
def main():
    """Run all Fileverse tests"""
    try:
        # Run health check first
        asyncio.run(test_fileverse_health())
        
        # Then run upload tests
        asyncio.run(test_fileverse_upload())
        
        logger.info("\n✅ All test suites passed!")
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Tests failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 