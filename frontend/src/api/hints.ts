import client from './client'

export interface HintStatus {
  challenge_slug: string
  revealed: number[]
  points_spent: number
}

export interface HintReveal {
  index: number
  text: string
  cost: number
  points_deducted: number
}

export const getHintStatus = async (slug: string): Promise<HintStatus> => {
  const res = await client.get<HintStatus>(`/hints/${slug}`)
  return res.data
}

export const revealHint = async (slug: string, index: number): Promise<HintReveal> => {
  const res = await client.post<HintReveal>(`/hints/${slug}/${index}`)
  return res.data
}
