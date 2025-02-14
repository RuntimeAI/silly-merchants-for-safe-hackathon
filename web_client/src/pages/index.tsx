import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Banner from '../components/Banner';
import StrategyPanel from '../components/StrategyPanel';
import BargainBazaar from '../components/BargainBazaar';

export default function Home() {
  const [gameEvents, setGameEvents] = useState<any[]>([]);
  const [isGameRunning, setIsGameRunning] = useState(false);

  const startGame = async (strategy: string) => {
    setIsGameRunning(true);
    setGameEvents([]);

    try {
      const response = await fetch('http://localhost:8000/merchants_1o1/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_advisory: strategy })
      });

      const reader = response.body?.getReader();
      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = new TextDecoder().decode(value);
        const events = text.split('\n\n')
          .filter(line => line.startsWith('data: '))
          .map(line => JSON.parse(line.replace('data: ', '')));

        setGameEvents(prev => [...prev, ...events]);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsGameRunning(false);
    }
  };

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