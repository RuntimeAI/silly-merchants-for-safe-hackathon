import axios from 'axios'
import { EventSourcePolyfill as EventSource } from 'event-source-polyfill'

export class GameRunner {
  private gameId: string | null = null
  private eventSource: EventSource | null = null
  private terminal: any

  constructor(terminal: any) {
    this.terminal = terminal
  }

  async createGame(): Promise<void> {
    try {
      const response = await axios.post('/merchants_1o1/games', null, {
        params: { debug: true }
      })
      this.gameId = response.data.game_id
      this.writeLine(`Game created with ID: ${this.gameId}`)
    } catch (error) {
      this.writeError('Failed to create game')
      throw error
    }
  }

  async startGame(): Promise<void> {
    if (!this.gameId) {
      this.writeError('No game created yet')
      return
    }

    try {
      await axios.post(`/merchants_1o1/games/${this.gameId}/start`, {
        strategy_advisory: "Play strategically and cooperatively"
      })
      this.writeLine('Game started successfully')
      this.subscribeToEvents()
    } catch (error) {
      this.writeError('Failed to start game')
      throw error
    }
  }

  private subscribeToEvents(): void {
    if (!this.gameId) return

    this.eventSource = new EventSource(
      `/merchants_1o1/games/${this.gameId}/events`
    )

    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.handleGameEvent(data)
    }

    this.eventSource.onerror = (error) => {
      this.writeError('Event stream error')
      this.cleanup()
    }
  }

  private handleGameEvent(event: any): void {
    switch (event.name) {
      case 'game_started':
        this.formatGameStart(event.data)
        break
      case 'round_started':
        this.formatRoundStart(event.data)
        break
      case 'player_thinking':
        this.formatPlayerThinking(event.data)
        break
      case 'player_action':
        this.formatPlayerAction(event.data)
        break
      case 'round_ended':
        this.formatRoundEnd(event.data)
        break
      case 'game_ended':
        this.formatGameEnd(event.data)
        this.cleanup()
        break
    }
  }

  private formatGameStart(data: any): void {
    this.writeLine('\n🎮 Game Started!')
    this.writeLine('Initial standings:')
    Object.entries(data.players).forEach(([player, coins]: [string, any]) => {
      this.writeLine(`  ${player}: ${coins} coins`)
    })
  }

  private formatRoundStart(data: any): void {
    this.writeLine(`\n📍 Round ${data.round} Started`)
  }

  private formatPlayerThinking(data: any): void {
    this.writeLine(`\n🤔 ${data.player} is thinking...`)
    if (data.thinking) {
      this.writeLine(data.thinking.split('\n').map((line: string) => `  ${line}`).join('\n'))
    }
  }

  private formatPlayerAction(data: any): void {
    this.writeLine(`\n💬 ${data.player}: ${data.action.message}`)
    if (data.action.transfers?.length) {
      data.action.transfers.forEach((transfer: any) => {
        this.writeLine(`  💰 Transferred ${transfer.amount} coins to ${transfer.recipient}`)
      })
    }
  }

  private formatRoundEnd(data: any): void {
    this.writeLine('\n🔚 Round End')
    this.writeLine('Standings:')
    Object.entries(data.standings).forEach(([player, coins]: [string, any]) => {
      this.writeLine(`  ${player}: ${coins} coins`)
    })
  }

  private formatGameEnd(data: any): void {
    this.writeLine('\n🏁 Game Over!')
    this.writeLine(`Winner: ${data.winner}`)
    this.writeLine('\nFinal Standings:')
    Object.entries(data.final_standings).forEach(([player, coins]: [string, any]) => {
      this.writeLine(`  ${player}: ${coins} coins`)
    })
    if (data.log_file_id) {
      this.writeLine(`\nGame log saved: https://api.singha.today/api/files/${data.log_file_id}`)
    }
  }

  private writeLine(text: string): void {
    this.terminal?.writeln(`\x1b[0m${text}`)
  }

  private writeError(text: string): void {
    this.terminal?.writeln(`\x1b[31m${text}\x1b[0m`)
  }

  private cleanup(): void {
    this.eventSource?.close()
    this.eventSource = null
    this.gameId = null
  }
} 