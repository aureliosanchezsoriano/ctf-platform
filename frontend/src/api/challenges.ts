import client from './client'
import type { Challenge, FlagResult } from './types'

export const getChallenges = async (): Promise<Challenge[]> => {
  const res = await client.get<Challenge[]>('/challenges')
  return res.data
}

export const getChallenge = async (slug: string): Promise<Challenge> => {
  const res = await client.get<Challenge>(`/challenges/${slug}`)
  return res.data
}

export const submitFlag = async (slug: string, flag: string): Promise<FlagResult> => {
  const res = await client.post<FlagResult>(`/challenges/${slug}/submit`, { flag })
  return res.data
}
