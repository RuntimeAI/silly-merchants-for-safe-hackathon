import { motion } from 'framer-motion';

export default function Banner() {
  return (
    <motion.header 
      className="p-8 border-b border-cyan-500/30"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h1 className="text-5xl font-cyber mb-2 text-center text-cyan-400">
        Silly Merchants
        <span className="text-pink-500">!</span>
      </h1>
      <h2 className="text-2xl text-center mb-4 text-cyan-300">
        Agent vs. Agent Arena (AAA)
      </h2>
      <div className="max-w-2xl mx-auto text-center text-cyan-200">
        <p>Welcome to the ultimate trading showdown between Marco Polo and Trader Joe!</p>
        <p>Each merchant starts with 10 coins. Through negotiation and strategy, try to accumulate the most wealth.</p>
      </div>
    </motion.header>
  );
} 