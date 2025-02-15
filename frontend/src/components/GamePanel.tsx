'use client'

import { useEffect, useRef, useState } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import { GameRunner } from '@/utils/gameRunner'

const GamePanel = () => {
  const terminalRef = useRef<HTMLDivElement>(null)
  const [terminal, setTerminal] = useState<Terminal | null>(null)
  const [strategy, setStrategy] = useState<string>(
    'Be strategic and cooperative in early rounds, but be prepared to adapt based on the opponent\'s behavior.'
  )
  const [isGameRunning, setIsGameRunning] = useState(false)
  const gameRunnerRef = useRef<GameRunner | null>(null)

  useEffect(() => {
    if (terminalRef.current && !terminal) {
      const term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
          background: '#1a1b26',
          foreground: '#a9b1d6',
        },
      })

      const fitAddon = new FitAddon()
      term.loadAddon(fitAddon)
      term.loadAddon(new WebLinksAddon())

      term.open(terminalRef.current)
      fitAddon.fit()

      term.writeln('🎮 Welcome to Silly Merchants Game Terminal!')
      term.writeln('Type your strategy and click Start Game to begin.')
      term.writeln('')

      setTerminal(term)
      gameRunnerRef.current = new GameRunner(term)

      const handleResize = () => fitAddon.fit()
      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
        term.dispose()
      }
    }
  }, [terminalRef, terminal])

  const startGame = async () => {
    if (!terminal || isGameRunning) return

    setIsGameRunning(true)
    try {
      await gameRunnerRef.current?.createGame()
      await gameRunnerRef.current?.startGame()
    } catch (error) {
      terminal.writeln('\x1b[31mError starting game: ' + error + '\x1b[0m')
    } finally {
      setIsGameRunning(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="bg-gray-900 rounded-lg p-6">
        <div className="mb-4">
          <label
            htmlFor="strategy"
            className="block text-white text-sm font-medium mb-2"
          >
            Your Strategy Advisory:
          </label>
          <textarea
            id="strategy"
            rows={4}
            className="w-full px-3 py-2 text-gray-200 bg-gray-800 rounded-md focus:ring-2 focus:ring-blue-500"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            disabled={isGameRunning}
          />
        </div>

        <button
          onClick={startGame}
          disabled={isGameRunning}
          className="mb-6 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          {isGameRunning ? 'Game Running...' : 'Start Game'}
        </button>

        <div
          ref={terminalRef}
          className="w-full h-[500px] rounded-lg overflow-hidden border border-gray-700"
        />
      </div>
    </div>
  )
}

export default GamePanel 