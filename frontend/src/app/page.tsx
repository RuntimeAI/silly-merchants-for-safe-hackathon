import GameBanner from '@/components/GameBanner'
import GameIntro from '@/components/GameIntro'
import GamePanel from '@/components/GamePanel'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100">
      <GameBanner />
      <GameIntro />
      <GamePanel />
    </main>
  )
} 