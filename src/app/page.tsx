import Banner from '@/components/Banner';
import GameIntro from '@/components/GameIntro';
import GamePlay from '@/components/GamePlay';

export default function Home() {
  return (
    <main className="min-h-screen">
      <Banner />
      <GameIntro />
      <GamePlay />
    </main>
  );
} 