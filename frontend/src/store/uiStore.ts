import { create } from 'zustand'

const FONT_SIZE_KEY = 'ctf_font_size'
const MIN_SIZE = 1
const MAX_SIZE = 1.5
const DEFAULT_SIZE = 1
const STEP = 0.1

interface UIState {
  scale: number
  increase: () => void
  decrease: () => void
  reset: () => void
}

function applyScale(scale: number) {
  document.documentElement.style.zoom = String(scale)
}

const saved = parseFloat(localStorage.getItem(FONT_SIZE_KEY) ?? String(DEFAULT_SIZE))
const initial = Math.min(MAX_SIZE, Math.max(MIN_SIZE, saved))
applyScale(initial)

export const useUIStore = create<UIState>((set, get) => ({
  scale: initial,

  increase: () => {
    const next = Math.min(MAX_SIZE, parseFloat((get().scale + STEP).toFixed(1)))
    localStorage.setItem(FONT_SIZE_KEY, String(next))
    applyScale(next)
    set({ scale: next })
  },

  decrease: () => {
    const next = Math.max(MIN_SIZE, parseFloat((get().scale - STEP).toFixed(1)))
    localStorage.setItem(FONT_SIZE_KEY, String(next))
    applyScale(next)
    set({ scale: next })
  },

  reset: () => {
    localStorage.setItem(FONT_SIZE_KEY, String(DEFAULT_SIZE))
    applyScale(DEFAULT_SIZE)
    set({ scale: DEFAULT_SIZE })
  },
}))