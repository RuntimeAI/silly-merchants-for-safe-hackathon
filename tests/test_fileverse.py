import asyncio
import logging
from src.utils.fileverse_client import FileverseClient
import json
import requests
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use specific test log file
LOGS_DIR = os.path.join('logs', 'merchants_1o1')
TEST_LOG_FILE = 'test.log'

async def test_fileverse_upload():
    """Test uploading content to Fileverse"""
    client = FileverseClient()
    
    try:
        # Use the test log file
        log_path = os.path.join(LOGS_DIR, TEST_LOG_FILE)
        
        if not os.path.exists(log_path):
            raise Exception(f"Test log file not found: {log_path}")
            
        logger.info(f"Using test log file: {log_path}")
        
        # Read log content
        with open(log_path, 'r') as f:
            log_content = f.read()
            
        # Generate test game ID
        test_game_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare test upload data
        game_data = {
            "timestamp": datetime.now().isoformat(),
            "game_id": test_game_id,
            "log_content": log_content,
            "metadata": {
                "game_type": "merchants_1o1",
                "log_file": TEST_LOG_FILE,
                "timestamp": datetime.now().isoformat(),
                "test": True
            }
        }
        
        # Test upload
        logger.info("\nTesting game log upload...")
        file_id = await client.save_game_log(test_game_id, game_data)
        logger.info(f"Successfully uploaded file with ID: {file_id}")
        
        # Test retrieval
        logger.info("\nTesting file retrieval...")
        retrieved = client.get_file(file_id)
        logger.info(f"Retrieved file details: {json.dumps(retrieved, indent=2)}")
        
        # Verify content
        if retrieved and retrieved.get('content'):
            uploaded_data = json.loads(retrieved['content'])
            assert uploaded_data['game_id'] == test_game_id, "Game ID mismatch"
            assert uploaded_data['log_content'] == log_content, "Log content mismatch"
            assert uploaded_data['metadata']['test'] == True, "Test metadata missing"
            logger.info("✅ Content verification passed!")
        
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