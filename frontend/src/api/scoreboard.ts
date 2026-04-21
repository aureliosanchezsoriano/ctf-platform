import client from './client'
import type { ScoreboardEntry } from './types'

export const getScoreboard = async (): Promise<ScoreboardEntry[]> => {
  const res = await client.get<ScoreboardEntry[]>('/scoreboard')
  return res.data
}
