export type UserRole = 'student' | 'teacher' | 'admin'

export interface AuthUser {
  id: string
  username: string
  full_name: string
  role: UserRole
  class_name: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  role: UserRole
  full_name: string
}

export interface Hint {
  index: number
  cost: number
  text: string
}

export interface Challenge {
  id: string
  slug: string
  name: string
  description: string
  type: 'docker' | 'file'
  category: string
  difficulty: 'easy' | 'medium' | 'hard'
  owasp_ref: string | null
  points: number
  is_required: boolean
  is_active: boolean
  flag_type: 'dynamic' | 'static'
  hints: Hint[]
  unlocks_after: string | null
  solved: boolean
  attempts_count: number
  locked: boolean
}

export interface FlagResult {
  correct: boolean
  message: string
  points_earned: number
}

export interface ScoreboardEntry {
  rank: number
  username: string
  full_name: string
  class_name: string | null
  points: number
  solved_count: number
  last_solve: string | null
}
