/**
 * Authentication State Management with Zustand
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { getCognitoAuth } from '../lib/cognito'

interface User {
  sub: string
  username: string
  email?: string
  emailVerified?: boolean
}

interface AuthTokens {
  accessToken: string
  idToken: string
  refreshToken: string
  expiresAt: number // Timestamp when token expires
}

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  signUp: (email: string, password: string) => Promise<void>
  confirmSignUp: (email: string, code: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => void
  refreshToken: () => Promise<void>
  forgotPassword: (email: string) => Promise<void>
  confirmPassword: (email: string, code: string, newPassword: string) => Promise<void>
  clearError: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      signUp: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const cognito = getCognitoAuth()
          await cognito.signUp(email, password)
          set({ isLoading: false })
          // User needs to verify email before signing in
        } catch (error: any) {
          set({ isLoading: false, error: error.message })
          throw error
        }
      },

      confirmSignUp: async (email: string, code: string) => {
        set({ isLoading: true, error: null })
        try {
          const cognito = getCognitoAuth()
          await cognito.confirmSignUp(email, code)
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false, error: error.message })
          throw error
        }
      },

      signIn: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const cognito = getCognitoAuth()
          const tokens = await cognito.signIn(email, password)

          // Decode access token to get user info
          const user = cognito.decodeToken(tokens.accessToken)

          if (!user) {
            throw new Error('Failed to decode user token')
          }

          // Calculate expiration timestamp
          const expiresAt = Date.now() + tokens.expiresIn * 1000

          set({
            user,
            tokens: {
              accessToken: tokens.accessToken,
              idToken: tokens.idToken,
              refreshToken: tokens.refreshToken,
              expiresAt
            },
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message,
            user: null,
            tokens: null,
            isAuthenticated: false
          })
          throw error
        }
      },

      signOut: () => {
        const cognito = getCognitoAuth()
        cognito.signOut()
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
          error: null
        })
      },

      refreshToken: async () => {
        const { tokens } = get()

        if (!tokens?.refreshToken) {
          throw new Error('No refresh token available')
        }

        try {
          const cognito = getCognitoAuth()
          const newTokens = await cognito.refreshToken(tokens.refreshToken)

          // Decode new access token
          const user = cognito.decodeToken(newTokens.accessToken)

          if (!user) {
            throw new Error('Failed to decode refreshed token')
          }

          // Calculate new expiration
          const expiresAt = Date.now() + newTokens.expiresIn * 1000

          set({
            user,
            tokens: {
              accessToken: newTokens.accessToken,
              idToken: newTokens.idToken,
              refreshToken: newTokens.refreshToken,
              expiresAt
            }
          })
        } catch (error: any) {
          // Refresh failed - sign out user
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            error: 'Session expired. Please sign in again.'
          })
          throw error
        }
      },

      forgotPassword: async (email: string) => {
        set({ isLoading: true, error: null })
        try {
          const cognito = getCognitoAuth()
          await cognito.forgotPassword(email)
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false, error: error.message })
          throw error
        }
      },

      confirmPassword: async (email: string, code: string, newPassword: string) => {
        set({ isLoading: true, error: null })
        try {
          const cognito = getCognitoAuth()
          await cognito.confirmPassword(email, code, newPassword)
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false, error: error.message })
          throw error
        }
      },

      clearError: () => {
        set({ error: null })
      },

      checkAuth: async () => {
        const { tokens, refreshToken } = get()

        if (!tokens) {
          set({ isAuthenticated: false })
          return
        }

        const cognito = getCognitoAuth()

        // Check if token is expired
        if (cognito.isTokenExpired(tokens.accessToken)) {
          // Try to refresh
          try {
            await refreshToken()
          } catch (error) {
            // Refresh failed - sign out
            set({
              user: null,
              tokens: null,
              isAuthenticated: false
            })
          }
        } else {
          // Token still valid
          set({ isAuthenticated: true })
        }
      }
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        // Only persist these fields
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

// Auto-check auth on app start
useAuthStore.getState().checkAuth()
