import { motion } from 'framer-motion';
import { useEffect, useRef } from 'react';

interface GameEvent {
  event: string;
  data: {
    player?: string;
    thinking?: string;
    message?: string;
    transfers?: Array<{
      recipient: string;
      amount: number;
    }>;
    standings?: Record<string, number>;
    round?: number;
    winner?: string;
    final_standings?: Record<string, number>;
    timestamp: string;
  };
}

interface BargainBazaarProps {
  events: GameEvent[];
}

export default function BargainBazaar({ events }: BargainBazaarProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const renderEvent = (event: GameEvent) => {
    switch (event.event) {
      case 'game_start':
        return (
          <motion.div 
            className="bg-gradient-to-r from-cyan-900/30 to-pink-900/30 p-4 rounded-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h4 className="text-lg font-cyber text-pink-500">Game Started!</h4>
            <div className="grid grid-cols-2 gap-4 mt-2">
              {Object.entries(event.data.standings || {}).map(([name, coins]) => (
                <div key={name} className="text-cyan-300">
                  <span className="font-bold">{name}:</span> {coins} coins
                </div>
              ))}
            </div>
          </motion.div>
        );

      case 'player_thinking':
        return (
          <motion.div 
            className={`p-4 rounded-lg bg-gray-800/50 ${
              event.data.player === 'Marco Polo' ? 'ml-0 mr-12' : 'ml-12 mr-0'
            }`}
            initial={{ opacity: 0, x: event.data.player === 'Marco Polo' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-pink-500">🤔 {event.data.player} thinking...</span>
            </div>
            <p className="text-cyan-200 whitespace-pre-wrap">{event.data.thinking}</p>
          </motion.div>
        );

      case 'player_action':
        return (
          <motion.div 
            className={`p-4 rounded-lg bg-gray-800/50 ${
              event.data.player === 'Marco Polo' ? 'ml-0 mr-12' : 'ml-12 mr-0'
            }`}
            initial={{ opacity: 0, x: event.data.player === 'Marco Polo' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-pink-500">{event.data.player}</span>
            </div>
            <p className="text-cyan-200">{event.data.message}</p>
            {event.data.transfers && event.data.transfers.length > 0 && (
              <div className="mt-2">
                <p className="text-pink-400">Transfers:</p>
                {event.data.transfers.map((transfer, idx) => (
                  <p key={idx} className="text-cyan-300">
                    {transfer.amount} coins to {transfer.recipient}
                  </p>
                ))}
              </div>
            )}
          </motion.div>
        );

      case 'round_summary':
        return (
          <motion.div 
            className="bg-gradient-to-r from-pink-900/30 to-cyan-900/30 p-4 rounded-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h4 className="text-lg font-cyber text-pink-500">
              Round {event.data.round} Summary
            </h4>
            <div className="mt-2">
              {Object.entries(event.data.standings || {}).map(([name, coins]) => (
                <div key={name} className="text-cyan-300">
                  <span className="font-bold">{name}:</span> {coins} coins
                </div>
              ))}
            </div>
          </motion.div>
        );

      case 'game_end':
        return (
          <motion.div 
            className="bg-gradient-to-r from-pink-500/30 to-cyan-500/30 p-4 rounded-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h4 className="text-lg font-cyber text-pink-500">Game Over!</h4>
            <p className="text-cyan-300 mt-2">
              Winner: <span className="font-bold">{event.data.winner}</span>
            </p>
            <div className="mt-2">
              {Object.entries(event.data.final_standings || {}).map(([name, coins]) => (
                <div key={name} className="text-cyan-300">
                  <span className="font-bold">{name}:</span> {coins} coins
                </div>
              ))}
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <motion.div 
      className="col-span-9 bg-gray-800 rounded-lg border border-cyan-500/30"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      <div className="p-4">
        <h3 className="text-xl font-cyber mb-4 text-pink-500">Bargain Bazaar</h3>
        <div className="h-[600px] overflow-y-auto space-y-4 mb-4 p-4">
          {events.map((event, index) => (
            <div key={index}>
              {renderEvent(event)}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </motion.div>
  );
} 