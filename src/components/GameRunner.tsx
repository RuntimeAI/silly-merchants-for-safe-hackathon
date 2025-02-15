import React, { useState, useRef } from 'react';
import { Terminal } from './Terminal';
import axios from 'axios';
import '../styles/GameRunner.css';

export const GameRunner: React.FC = () => {
    const [strategy, setStrategy] = useState<string>(
        "Strategy for Marco Polo:\n" +
        "- Build trust in early rounds\n" +
        "- Be cautious with large transfers\n" +
        "- Look for opportunities to cooperate\n" +
        "- Consider betrayal only if heavily betrayed"
    );
    const [isRunning, setIsRunning] = useState(false);
    const terminalRef = useRef<any>(null);
    
    const writeLine = (text: string, color: string = 'white') => {
        terminalRef.current?.writeln(`\x1b[${color === 'white' ? '0' : '1;32'}m${text}\x1b[0m`);
    };
    
    const writeError = (text: string) => {
        terminalRef.current?.writeln(`\x1b[31m${text}\x1b[0m`);
    };
    
    const runGame = async () => {
        if (isRunning) return;
        setIsRunning(true);
        
        try {
            // Create game
            writeLine('Creating new game in DEBUG mode...', 'green');
            const createResponse = await axios.post('/merchants_1o1/games', null, {
                params: { debug: true }
            });
            const gameId = createResponse.data.game_id;
            writeLine(`Created game: ${gameId}`, 'green');
            
            // Start game
            writeLine('Starting game...', 'green');
            await axios.post(`/merchants_1o1/games/${gameId}/start`, {
                strategy_advisory: strategy
            });
            writeLine('Game started successfully', 'green');
            
            // Subscribe to events
            writeLine('Subscribing to game events...', 'green');
            const eventSource = new EventSource(`/merchants_1o1/games/${gameId}/events`);
            
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                formatEvent(data);
                
                // Close connection when game ends
                if (data.name === 'game_ended') {
                    eventSource.close();
                    setIsRunning(false);
                }
            };
            
            eventSource.onerror = (error) => {
                writeError(`Error in event subscription: ${error}`);
                eventSource.close();
                setIsRunning(false);
            };
            
        } catch (error) {
            writeError(`Error: ${error}`);
            setIsRunning(false);
        }
    };
    
    const formatEvent = (event: any) => {
        const timestamp = new Date().toLocaleTimeString();
        
        switch (event.name) {
            case 'game_started':
                writeLine(`\n🎮 Game Started at ${timestamp}`);
                writeLine('Initial standings:');
                Object.entries(event.data.players).forEach(([player, coins]: [string, any]) => {
                    writeLine(`  ${player}: ${coins} coins`);
                });
                break;
                
            case 'round_started':
                writeLine(`\n📍 Round ${event.data.round} Started`);
                break;
                
            case 'player_thinking':
                writeLine(`\n🤔 ${event.data.player} is thinking...`);
                if (event.data.thinking) {
                    writeLine(event.data.thinking);
                }
                break;
                
            case 'player_action':
                writeLine(`\n💬 ${event.data.player}: ${event.data.action.message}`);
                if (event.data.action.transfers?.length) {
                    event.data.action.transfers.forEach((transfer: any) => {
                        writeLine(`  💰 Transferred ${transfer.amount} coins to ${transfer.recipient}`);
                    });
                }
                break;
                
            case 'round_ended':
                writeLine('\n🔚 Round End');
                writeLine('Standings:');
                Object.entries(event.data.standings).forEach(([player, coins]: [string, any]) => {
                    writeLine(`  ${player}: ${coins} coins`);
                });
                break;
                
            case 'game_ended':
                writeLine('\n🏁 Game Over!');
                writeLine(`Winner: ${event.data.winner}`);
                writeLine('\nFinal Standings:');
                Object.entries(event.data.final_standings).forEach(([player, coins]: [string, any]) => {
                    writeLine(`  ${player}: ${coins} coins`);
                });
                if (event.data.log_file_id) {
                    writeLine(`\nGame log saved: https://api.singha.today/api/files/${event.data.log_file_id}`);
                }
                break;
        }
    };
    
    return (
        <div className="game-runner">
            <div className="controls">
                <textarea
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                    placeholder="Enter strategy..."
                    disabled={isRunning}
                />
                <button 
                    onClick={runGame}
                    disabled={isRunning}
                >
                    {isRunning ? 'Game Running...' : 'Start Game'}
                </button>
            </div>
            <Terminal ref={terminalRef} />
        </div>
    );
}; 