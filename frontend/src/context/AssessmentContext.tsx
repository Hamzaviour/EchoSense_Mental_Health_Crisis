import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import api from '@/api/client'

export interface AssessmentSessionState {
  session_id: number
  status: string
  progress_percent?: number
  current_question?: { id: number; number: number; text: string; options: { value: number; label: string }[] }
  current_type_label?: string
  type_progress?: string
  answered_count?: number
  total_questions?: number
  is_complete?: boolean
}

interface AssessmentCtx {
  session: AssessmentSessionState | null
  sidebarExpanded: boolean
  sidebarCollapsed: boolean
  saving: boolean
  loadActiveSession: () => Promise<void>
  acceptOffer: (sessionId: number) => Promise<void>
  declineOffer: (sessionId: number) => Promise<void>
  saveAnswer: (questionId: number, value: number) => Promise<void>
  setOfferFromChat: (offer: { offered?: boolean; session_id?: number; types?: string[] }) => void
  toggleCollapsed: () => void
  setSidebarExpanded: (v: boolean) => void
}

const AssessmentContext = createContext<AssessmentCtx | null>(null)

export function AssessmentProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AssessmentSessionState | null>(null)
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [saving, setSaving] = useState(false)

  const loadActiveSession = useCallback(async () => {
    try {
      const { data } = await api.get('/api/assessments/sessions/active')
      if (data.session?.status === 'IN_PROGRESS') {
        setSession(data.session)
        setSidebarExpanded(true)
        setSidebarCollapsed(false)
      }
    } catch { /* none */ }
  }, [])

  const acceptOffer = useCallback(async (sessionId: number) => {
    const { data } = await api.post(`/api/assessments/sessions/${sessionId}/accept`)
    setSession(data.session)
    setSidebarExpanded(true)
    setSidebarCollapsed(false)
  }, [])

  const declineOffer = useCallback(async (sessionId: number) => {
    await api.post(`/api/assessments/sessions/${sessionId}/decline`)
  }, [])

  const saveAnswer = useCallback(async (questionId: number, value: number) => {
    if (!session?.session_id) return
    setSaving(true)
    try {
      const { data } = await api.patch(`/api/assessments/sessions/${session.session_id}/answers`, {
        question_id: questionId,
        value,
      })
      setSession(data.session)
      if (data.session?.is_complete) setSidebarCollapsed(true)
    } finally {
      setSaving(false)
    }
  }, [session?.session_id])

  const setOfferFromChat = useCallback(() => {}, [])

  const toggleCollapsed = () => setSidebarCollapsed((c) => !c)

  return (
    <AssessmentContext.Provider
      value={{
        session,
        sidebarExpanded,
        sidebarCollapsed,
        saving,
        loadActiveSession,
        acceptOffer,
        declineOffer,
        saveAnswer,
        setOfferFromChat,
        toggleCollapsed,
        setSidebarExpanded,
      }}
    >
      {children}
    </AssessmentContext.Provider>
  )
}

export const useAssessment = () => {
  const ctx = useContext(AssessmentContext)
  if (!ctx) throw new Error('useAssessment must be used within AssessmentProvider')
  return ctx
}
