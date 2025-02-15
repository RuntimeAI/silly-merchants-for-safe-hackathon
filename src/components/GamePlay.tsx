'use client';

import { useEffect, useRef, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import 'xterm/css/xterm.css';

const GamePlay = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [strategy, setStrategy] = useState(
    "Strategy for Marco Polo:\n" +
    "- Build trust in early rounds\n" +
    "- Be cautious with large transfers\n" +
    "- Look for opportunities to cooperate\n" +
    "- Consider betrayal only if heavily betrayed"
  );
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);

  useEffect(() => {
    if (!terminalRef.current || xtermRef.current) return;

    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#1a1a2e',
        foreground: '#d4d4d4',
        cursor: '#d4d4d4'
      }
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());

    term.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = term;

    const handleResize = () => fitAddon.fit();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
    };
  }, []);

  const writeLine = (text: string, color: string = 'white') => {
    xtermRef.current?.writeln(
      `\x1b[${color === 'white' ? '0' : '1;32'}m${text}\x1b[0m`
    );
  };

  const writeError = (text: string) => {
    xtermRef.current?.writeln(`\x1b[31m${text}\x1b[0m`);
  };

  const runGame = async () => {
    if (isRunning) return;
    setIsRunning(true);

    try {
      // Create game
      writeLine('Creating new game...', 'green');
      const createResponse = await fetch('/merchants_1o1/games?debug=true', {
        method: 'POST'
      });
      const gameData = await createResponse.json();
      const gameId = gameData.game_id;
      writeLine(`Created game: ${gameId}`, 'green');

      // Start game
      writeLine('Starting game...', 'green');
      await fetch(`/merchants_1o1/games/${gameId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ strategy_advisory: strategy })
      });
      writeLine('Game started successfully', 'green');

      // Subscribe to events
      writeLine('Subscribing to game events...', 'green');
      const eventSource = new EventSource(
        `/merchants_1o1/games/${gameId}/events`
      );

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        formatEvent(data);

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
        break;
    }
  };

  return (
    <div className="py-16 px-4 bg-gray-100">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="mb-6">
            <textarea
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full h-40 p-4 border rounded-lg font-mono text-sm"
              placeholder="Enter strategy..."
              disabled={isRunning}
            />
          </div>
          <button
            onClick={runGame}
            disabled={isRunning}
            className="mb-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isRunning ? 'Game Running...' : 'Start Game'}
          </button>
          <div
            ref={terminalRef}
            className="w-full h-[500px] rounded-lg overflow-hidden border border-gray-200"
          />
        </div>
      </div>
    </div>
  );
};

export default GamePlay; 