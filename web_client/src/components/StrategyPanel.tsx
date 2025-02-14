import { useState } from 'react';
import { motion } from 'framer-motion';

const defaultStrategy = `Strategy for Marco Polo:
- Build trust early but be cautious
- Focus on long-term gains
- Be adaptive to opponent's behavior
- Balance cooperation and competition`;

interface StrategyPanelProps {
  onStart: (strategy: string) => void;
  isGameRunning: boolean;
}

export default function StrategyPanel({ onStart, isGameRunning }: StrategyPanelProps) {
  const [strategy, setStrategy] = useState(defaultStrategy);

  return (
    <motion.div 
      className="col-span-3 space-y-4"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      <div className="bg-gray-800 p-4 rounded-lg border border-cyan-500/30">
        <h3 className="text-xl font-cyber mb-4 text-pink-500">Strategy Playbook</h3>
        <textarea
          value={strategy}
          onChange={(e) => setStrategy(e.target.value)}
          className="w-full h-48 bg-gray-900 text-cyan-300 p-3 rounded border border-cyan-500/30 focus:border-pink-500 focus:ring-1 focus:ring-pink-500"
          maxLength={400}
          placeholder="Enter your strategy..."
        />
        <div className="text-right text-sm text-cyan-400">
          {strategy.split(' ').length}/80 words
        </div>
        <button
          onClick={() => onStart(strategy)}
          disabled={isGameRunning}
          className={`w-full mt-4 py-2 px-4 rounded font-cyber
            ${isGameRunning 
              ? 'bg-gray-700 text-gray-500' 
              : 'bg-pink-600 hover:bg-pink-700 text-white'}`}
        >
          {isGameRunning ? 'Game in Progress...' : 'Start dealing business!'}
        </button>
      </div>
    </motion.div>
  );
} 