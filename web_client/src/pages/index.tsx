import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Banner from '../components/Banner';
import StrategyPanel from '../components/StrategyPanel';
import BargainBazaar from '../components/BargainBazaar';

export default function Home() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [gameEvents, setGameEvents] = useState<any[]>([]);
  const [isGameRunning, setIsGameRunning] = useState(false);

  const createGame = async () => {
    const response = await fetch('http://localhost:8000/merchants_1o1/games', {
      method: 'POST'
    });
    const data = await response.json();
    setGameId(data.game_id);
  };

  const startGame = async (strategy: string) => {
    if (!gameId) {
      console.error('No game ID');
      return;
    }

    setIsGameRunning(true);
    setGameEvents([]);

    try {
      // Start game
      await fetch(`http://localhost:8000/merchants_1o1/games/${gameId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy })
      });

      // Subscribe to events
      const eventSource = new EventSource(
        `http://localhost:8000/merchants_1o1/games/${gameId}/events`
      );

      eventSource.onmessage = (event) => {
        const eventData = JSON.parse(event.data);
        setGameEvents(prev => [...prev, eventData]);
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
        setIsGameRunning(false);
      };

    } catch (error) {
      console.error('Error:', error);
      setIsGameRunning(false);
    }
  };

  useEffect(() => {
    createGame();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-cyan-300">
      <Banner />
      <div className="container mx-auto p-4 grid grid-cols-12 gap-4">
        <StrategyPanel 
          onStart={startGame} 
          isGameRunning={isGameRunning} 
        />
        <BargainBazaar events={gameEvents} />
      </div>
    </div>
  );
} 