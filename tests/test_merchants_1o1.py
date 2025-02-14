import pytest
from fastapi.testclient import TestClient
from src.api.server import app
import json

client = TestClient(app)

def test_game_initiation():
    response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": "Test strategy"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

def test_game_stream():
    # First initiate a game
    init_response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": "Test strategy"}
    )
    assert init_response.status_code == 200
    
    # Get the game ID from the first event
    events = init_response.iter_lines()
    first_event = next(events)
    event_data = json.loads(first_event.decode().replace("data: ", ""))
    assert event_data["type"] == "game_start"
    
    # Test different event types
    event_types = set()
    for line in events:
        if line:
            event = json.loads(line.decode().replace("data: ", ""))
            event_types.add(event["type"])
    
    # Verify we get all expected event types
    expected_types = {
        "game_start",
        "round_start",
        "player_thinking",
        "player_action",
        "round_summary",
        "game_end"
    }
    assert expected_types.issubset(event_types)

def test_invalid_strategy():
    # Test strategy that's too long
    long_strategy = "word " * 100
    response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": long_strategy}
    )
    assert response.status_code == 400

def test_game_events_format():
    response = client.post(
        "/merchants_1o1/initiate",
        json={"strategy_advisory": "Test strategy"}
    )
    
    for line in response.iter_lines():
        if line:
            event = json.loads(line.decode().replace("data: ", ""))
            # Check event structure
            assert "type" in event
            assert "content" in event
            
            # Check specific event types
            if event["type"] == "player_action":
                content = event["content"]
                assert "message" in content
                assert "transfers" in content
            elif event["type"] == "round_summary":
                content = event["content"]
                assert "final_status" in content
                assert "events" in content 