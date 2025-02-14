import pytest
from fastapi.testclient import TestClient

def test_initiate_game(client: TestClient, sample_strategy: str):
    """Test game initiation endpoint"""
    response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": sample_strategy}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "game_id" in data
    assert data["status"] == "initiated"
    assert isinstance(data["standings"], dict)
    assert len(data["log_messages"]) > 0
    assert "Marco Polo" in data["standings"]
    assert "Trader Joe" in data["standings"]

def test_initiate_game_long_strategy(client: TestClient):
    """Test game initiation with too long strategy"""
    long_strategy = " ".join(["word"] * 100)  # 100 words
    response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": long_strategy}
    )
    
    assert response.status_code == 400
    assert "Strategy advisory must be less than 80 words" in response.json()["detail"]

def test_get_game_status(client: TestClient, sample_strategy: str):
    """Test game status endpoint"""
    # First create a game
    init_response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": sample_strategy}
    )
    game_id = init_response.json()["game_id"]
    
    # Then get its status
    response = client.get(f"/merchants_1o1/{game_id}/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == game_id
    assert data["status"] == "in_progress"
    assert isinstance(data["standings"], dict)
    assert len(data["log_messages"]) >= 0

def test_get_nonexistent_game_status(client: TestClient):
    """Test getting status of non-existent game"""
    response = client.get("/merchants_1o1/nonexistent-id/status")
    
    assert response.status_code == 404
    assert "Game not found" in response.json()["detail"]

def test_run_game(client: TestClient, sample_strategy: str):
    """Test running a complete game"""
    # First create a game
    init_response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": sample_strategy}
    )
    game_id = init_response.json()["game_id"]
    
    # Then run it
    response = client.post(f"/merchants_1o1/{game_id}/run")
    
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == game_id
    assert data["status"] == "completed"
    assert "winner" in data
    assert isinstance(data["final_standings"], dict)
    assert len(data["log_messages"]) > 0

def test_run_nonexistent_game(client: TestClient):
    """Test running a non-existent game"""
    response = client.post("/merchants_1o1/nonexistent-id/run")
    
    assert response.status_code == 404
    assert "Game not found" in response.json()["detail"]

def test_game_cleanup_after_run(client: TestClient, sample_strategy: str):
    """Test that game is cleaned up after running"""
    # Create and run a game
    init_response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": sample_strategy}
    )
    game_id = init_response.json()["game_id"]
    
    # Run the game
    client.post(f"/merchants_1o1/{game_id}/run")
    
    # Try to get status of completed game
    response = client.get(f"/merchants_1o1/{game_id}/status")
    assert response.status_code == 404
    assert "Game not found" in response.json()["detail"] 