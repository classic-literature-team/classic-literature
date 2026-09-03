import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

interface UiState {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

/**
 * 전역 UI 상태(테마 등). localStorage에 persist 된다.
 */
export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: 'light',
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'ui-storage' },
  ),
)
