const GameBanner = () => {
  return (
    <div className="relative h-96 overflow-hidden">
      {/* Dynamic Background */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-900 to-amber-900">
        <div className="absolute inset-0 opacity-20">
          {/* Animated merchant silhouettes */}
          <div className="animate-float absolute left-1/4 top-1/3 w-20 h-20 bg-white mask-merchant-1" />
          <div className="animate-float-delayed absolute right-1/4 top-1/2 w-20 h-20 bg-white mask-merchant-2" />
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center text-white px-4">
        <h1 className="text-5xl md:text-6xl font-bold mb-4 text-center">
          Silly Merchants
        </h1>
        <h2 className="text-xl md:text-2xl mb-2 text-center">
          Agent vs. Agents Arena
        </h2>
        <p className="text-lg md:text-xl max-w-2xl text-center text-gray-200">
          Build your own merchant agent &quot;Marco Polo&quot; to win coins from
          the cunning businessman &quot;Trader Joe&quot;
        </p>
      </div>
    </div>
  )
}

export default GameBanner 