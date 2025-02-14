import os
from dotenv import load_dotenv
from src.spaces.silly_merchants_multiplayer_arena.runtime.trading import TradingRuntime
from src.spaces.silly_merchants_multiplayer_arena.agents.merchant import MerchantAgent
from src.core.config import GameConfig

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize game config
    config = GameConfig(
        max_rounds=int(os.getenv("MAX_ROUNDS", 100)),
        initial_balance=float(os.getenv("INITIAL_BALANCE", 1000.0)),
        trading_fee=float(os.getenv("TRADING_FEE", 0.01))
    )
    
    # Initialize game runtime
    game = TradingRuntime()
    
    # Create and register multiple agents
    agent_configs = [
        {"name": f"Merchant {i}", "strategy": "random"}
        for i in range(5)  # Create 5 agents
    ]
    
    for i, agent_config in enumerate(agent_configs):
        game.register_agent(f"agent{i+1}", agent_config)
    
    # Run the game
    for round in range(config.max_rounds):
        state = game.step()
        print(f"Round {round + 1}: {state}")
        
    # Print final results
    final_state = game.get_state()
    print("\nGame Over!")
    print(f"Final State: {final_state}")

if __name__ == "__main__":
    main() 