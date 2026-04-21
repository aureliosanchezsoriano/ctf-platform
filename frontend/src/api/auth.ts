import client from './client'
import type { LoginRequest, TokenResponse, AuthUser } from './types'

export const login = async (data: LoginRequest): Promise<TokenResponse> => {
  const res = await client.post<TokenResponse>('/auth/login', data)
  return res.data
}

export const getMe = async (token?: string): Promise<AuthUser> => {
  const res = await client.get<AuthUser>('/auth/me', {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
  return res.data
}
