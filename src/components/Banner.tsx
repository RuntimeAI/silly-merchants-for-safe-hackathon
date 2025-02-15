'use client';

import { useEffect, useRef } from 'react';

const Banner = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const setCanvasSize = () => {
      canvas.width = window.innerWidth;
      canvas.height = 400;
    };
    setCanvasSize();
    window.addEventListener('resize', setCanvasSize);

    // Animation variables
    let coins: { x: number; y: number; speed: number; size: number }[] = [];
    const coinCount = 50;

    // Initialize coins
    for (let i = 0; i < coinCount; i++) {
      coins.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        speed: 0.5 + Math.random() * 2,
        size: 10 + Math.random() * 20,
      });
    }

    // Animation function
    const animate = () => {
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw coins
      coins.forEach((coin) => {
        ctx.beginPath();
        ctx.arc(coin.x, coin.y, coin.size, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 215, 0, 0.3)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 215, 0, 0.8)';
        ctx.stroke();

        // Move coins
        coin.y += coin.speed;
        if (coin.y > canvas.height + coin.size) {
          coin.y = -coin.size;
          coin.x = Math.random() * canvas.width;
        }
      });

      requestAnimationFrame(animate);
    };

    animate();

    return () => window.removeEventListener('resize', setCanvasSize);
  }, []);

  return (
    <div className="relative h-[400px] overflow-hidden">
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full"
      />
      <div className="relative z-10 h-full flex flex-col items-center justify-center text-white px-4">
        <h1 className="text-5xl font-bold mb-4 text-center">
          Silly Merchants
          <span className="block text-3xl mt-2">Agent vs. Agents Arena</span>
        </h1>
        <p className="text-xl text-center max-w-2xl">
          Build your own merchant agent "Marco Polo" to win coins from the cunning
          businessman "Trader Joe".
        </p>
      </div>
    </div>
  );
};

export default Banner; 