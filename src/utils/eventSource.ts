export class GameEventSource {
    private eventSource: EventSource | null = null;
    
    constructor(private gameId: string) {}
    
    connect(handlers: {
        onGameStart?: (data: any) => void;
        onRoundStart?: (data: any) => void;
        onPlayerThinking?: (data: any) => void;
        onPlayerAction?: (data: any) => void;
        onRoundEnd?: (data: any) => void;
        onGameEnd?: (data: any) => void;
        onSystemStatus?: (data: any) => void;
        onError?: (error: any) => void;
    }) {
        this.eventSource = new EventSource(
            `/merchants_1o1/games/${this.gameId}/events`
        );
        
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.name) {
                case 'game_started':
                    handlers.onGameStart?.(data.data);
                    break;
                case 'round_started':
                    handlers.onRoundStart?.(data.data);
                    break;
                case 'player_thinking':
                    handlers.onPlayerThinking?.(data.data);
                    break;
                case 'player_action':
                    handlers.onPlayerAction?.(data.data);
                    break;
                case 'round_ended':
                    handlers.onRoundEnd?.(data.data);
                    break;
                case 'game_ended':
                    handlers.onGameEnd?.(data.data);
                    break;
                case 'system_status':
                    handlers.onSystemStatus?.(data.data);
                    break;
                case 'error':
                    handlers.onError?.(data.data);
                    break;
            }
        };
        
        this.eventSource.onerror = (error) => {
            handlers.onError?.(error);
        };
    }
    
    disconnect() {
        this.eventSource?.close();
        this.eventSource = null;
    }
} 