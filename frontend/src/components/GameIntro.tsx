const GameIntro = () => {
  return (
    <div className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Story Section */}
          <div className="bg-blue-50 p-8 rounded-lg">
            <h2 className="text-2xl font-bold mb-4 text-blue-900">The Story</h2>
            <p className="text-blue-800">
              In the bustling ports of the Mediterranean, two legendary merchants
              cross paths: Marco Polo, the brilliant explorer with an uncanny
              ability to read markets, and Trader Joe, a shrewd businessman known
              for his cunning deals. Both bald as the moon reflecting on the
              sea&apos;s surface, these 地中海商人 (Mediterranean merchants) engage
              in a battle of wits, each seeking to outmaneuver the other in a
              high-stakes game of trade and trust.
            </p>
          </div>

          {/* Rules Section */}
          <div className="bg-amber-50 p-8 rounded-lg">
            <h2 className="text-2xl font-bold mb-4 text-amber-900">
              Rules & How to Play
            </h2>
            <div className="space-y-4 text-amber-800">
              <p>
                <strong>Game Structure:</strong>
                <br />• 5 rounds of strategic trading
                <br />• Each player starts with 10 coins
              </p>
              <p>
                <strong>Your Role:</strong>
                <br />• Control Marco Polo by setting his strategy
                <br />• Make decisions about coin transfers
                <br />• Build trust or plan betrayals
              </p>
              <p>
                <strong>Winning Condition:</strong>
                <br />• The merchant with the most coins at the end wins
                <br />• Strategy and timing are crucial
              </p>
              <p>
                <strong>How to Start:</strong>
                <br />• Write your strategy in the game panel
                <br />• Click &quot;Start Game&quot; to begin
                <br />• Watch the trading unfold in real-time
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GameIntro 