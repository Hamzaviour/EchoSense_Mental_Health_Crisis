import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from '@/api/client'

interface User {
  id: number
  email: string
  role: string
}

interface AuthCtx {
  user: User | null
  profile: Record<string, unknown> | null
  loading: boolean
  login: (email: string, password: string) => Promise<unknown>
  register: (form: Record<string, unknown>) => Promise<unknown>
  logout: () => void
  setProfile: (p: Record<string, unknown> | null) => void
}

const AuthContext = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const saved = localStorage.getItem('user')
    if (token && saved) {
      setUser(JSON.parse(saved))
      setProfile(JSON.parse(localStorage.getItem('profile') || 'null'))
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/api/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    const prof = data.patient || data.counselor || null
    localStorage.setItem('profile', JSON.stringify(prof))
    setUser(data.user)
    setProfile(prof)
    return data
  }

  const register = async (form: Record<string, unknown>) => {
    const { data } = await api.post('/api/auth/register', form)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    localStorage.setItem('profile', JSON.stringify(data.patient))
    setUser(data.user)
    setProfile(data.patient)
    return data
  }

  const logout = () => {
    localStorage.clear()
    setUser(null)
    setProfile(null)
  }

  return (
    <AuthContext.Provider value={{ user, profile, loading, login, register, logout, setProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
