import React, { useEffect, useState } from 'react';
import { GameEventSource } from '../utils/eventSource';

interface PlayerStanding {
    coins: number;
}

interface GameState {
    standings: {
        [player: string]: number;
    };
    currentRound: number;
    messages: Array<{
        round: number;
        speaker: string;
        message: string;
        thinking?: string;
    }>;
    systemStatus: string;
}

export const GameDisplay: React.FC<{ gameId: string }> = ({ gameId }) => {
    const [gameState, setGameState] = useState<GameState>({
        standings: {},
        currentRound: 0,
        messages: [],
        systemStatus: ''
    });
    
    useEffect(() => {
        const eventSource = new GameEventSource(gameId);
        
        eventSource.connect({
            onGameStart: (data) => {
                setGameState(prev => ({
                    ...prev,
                    standings: data.players
                }));
            },
            
            onRoundStart: (data) => {
                setGameState(prev => ({
                    ...prev,
                    currentRound: data.round,
                    standings: data.standings
                }));
            },
            
            onPlayerThinking: (data) => {
                setGameState(prev => ({
                    ...prev,
                    messages: [...prev.messages, {
                        round: data.round,
                        speaker: data.player,
                        thinking: data.thinking,
                        message: 'Thinking...'
                    }]
                }));
            },
            
            onPlayerAction: (data) => {
                setGameState(prev => ({
                    ...prev,
                    messages: [...prev.messages, {
                        round: data.round,
                        speaker: data.player,
                        message: data.action.message
                    }]
                }));
            },
            
            onRoundEnd: (data) => {
                setGameState(prev => ({
                    ...prev,
                    standings: data.standings
                }));
            },
            
            onSystemStatus: (data) => {
                setGameState(prev => ({
                    ...prev,
                    systemStatus: `${data.action}: ${data.status}`
                }));
            },
            
            onGameEnd: (data) => {
                setGameState(prev => ({
                    ...prev,
                    standings: data.final_standings,
                    systemStatus: `Game Over! Winner: ${data.winner}`
                }));
            }
        });
        
        return () => eventSource.disconnect();
    }, [gameId]);
    
    return (
        <div className="game-display">
            {/* Game Status */}
            <div className="game-status">
                <h2>Round {gameState.currentRound}</h2>
                <p className="system-status">{gameState.systemStatus}</p>
            </div>
            
            {/* Standings */}
            <div className="standings">
                <h3>Current Standings</h3>
                {Object.entries(gameState.standings).map(([player, coins]) => (
                    <div key={player} className="player-standing">
                        <span className="player-name">{player}</span>
                        <span className="coin-count">{coins} coins</span>
                    </div>
                ))}
            </div>
            
            {/* Game Messages */}
            <div className="message-log">
                <h3>Game Log</h3>
                {gameState.messages.map((msg, index) => (
                    <div key={index} className="message">
                        <div className="message-header">
                            <span className="round">Round {msg.round}</span>
                            <span className="speaker">{msg.speaker}</span>
                        </div>
                        {msg.thinking && (
                            <div className="thinking">
                                <pre>{msg.thinking}</pre>
                            </div>
                        )}
                        <div className="message-content">
                            {msg.message}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}; 