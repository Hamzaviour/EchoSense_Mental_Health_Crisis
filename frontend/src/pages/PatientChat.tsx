import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import api from '@/api/client'
import AppLayout from '@/components/layout/AppLayout'
import ChatPanel, { ChatMessage } from '@/components/chat/ChatPanel'
import ConsentModal from '@/components/ConsentModal'
import AssessmentSidebar from '@/components/AssessmentSidebar'
import RiskBadge from '@/components/RiskBadge'
import VoiceRecorder from '@/components/VoiceRecorder'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useAssessment } from '@/context/AssessmentContext'
import { useLanguage } from '@/context/LanguageContext'
import MotivationalQuotesTicker from '@/components/patient/MotivationalQuotesTicker'
import { usePatientSocket } from '@/hooks/useSocket'

const humanDelay = (text: string) => Math.min(2200, 600 + text.length * 12)

export default function PatientChat() {
  const { language, t } = useLanguage()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [greeting, setGreeting] = useState('')
  const [risk, setRisk] = useState<{ level: string; score: number } | null>(null)
  const [consentOpen, setConsentOpen] = useState(false)
  const [lastOffer, setLastOffer] = useState<{ offered?: boolean; session_id?: number } | null>(null)
  const [loading, setLoading] = useState(false)
  const [typing, setTyping] = useState(false)
  const [error, setError] = useState('')
  const [crisisMode, setCrisisMode] = useState(false)
  const [counselorActive, setCounselorActive] = useState(false)
  const [patientDbId, setPatientDbId] = useState<number | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { loadActiveSession, sidebarExpanded, session } = useAssessment()

  usePatientSocket(patientDbId, (msg) => {
    setMessages((m) => {
      if (msg.id && m.some((x) => x.id === msg.id)) return m
      return [...m, msg]
    })
    if (msg.role === 'COUNSELOR') setCounselorActive(true)
  }, (msg) => {
    setCounselorActive(true)
    setMessages((m) => {
      if (msg.id && m.some((x) => x.id === msg.id)) return m
      return [...m, msg]
    })
  })

  useEffect(() => {
    load()
    loadActiveSession()
  }, [])

  useEffect(() => {
    if (!consentOpen) {
      api.get('/api/chat/greeting').then((g) => setGreeting(g.data.greeting)).catch(() => {})
    }
  }, [language, consentOpen])

  const load = async () => {
    try {
      const prof = await api.get('/api/patient/profile')
      if (prof.data.id) setPatientDbId(prof.data.id)
      if (!prof.data.consent_given) setConsentOpen(true)
      const g = await api.get('/api/chat/greeting')
      setGreeting(g.data.greeting)
      const hist = await api.get('/api/chat/history')
      setMessages(hist.data.messages || [])
      if (prof.data.latest_risk_level) {
        setRisk({ level: prof.data.latest_risk_level, score: prof.data.latest_risk_score })
      }
      setCounselorActive(prof.data.counselor_active === true)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { code?: string } } }
      if (err.response?.data?.code === 'CONSENT_REQUIRED') setConsentOpen(true)
    }
  }

  const handleConsent = async (data: { consent: boolean; privacy_accepted: boolean }) => {
    await api.post('/api/patient/consent', data)
    setConsentOpen(false)
    load()
  }

  const showAssistantWithDelay = async (data: {
    assistant_message?: string | null
    user_message_id: number
    risk: { level: string; score: number }
    assessment_offer?: { offered?: boolean; session_id?: number } | null
    crisis_mode?: boolean
    counselor_active?: boolean
    ai_active?: boolean
  }) => {
    setRisk(data.risk)
    if (data.counselor_active || data.ai_active === false) {
      setCounselorActive(true)
    }
    if (data.crisis_mode) {
      setCrisisMode(true)
      setLastOffer(null)
    } else if (data.assessment_offer) {
      setLastOffer(data.assessment_offer)
    } else {
      setLastOffer(null)
    }
    if (!data.assistant_message) return
    const assistantText = data.assistant_message
    setTyping(true)
    await new Promise((r) => setTimeout(r, humanDelay(assistantText)))
    setTyping(false)
    setMessages((m) => [
      ...m,
      { role: 'ASSISTANT', content: assistantText, id: data.user_message_id + 1 },
    ])
  }

  const sendMessage = async (content: string) => {
    if (!content.trim()) return
    setLoading(true)
    setError('')
    setMessages((m) => [...m, { role: 'PATIENT', content, id: Date.now() }])
    setInput('')
    try {
      const { data } = await api.post('/api/chat/message', { content, language })
      await showAssistantWithDelay(data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { code?: string; error?: string } } }
      if (err.response?.data?.code === 'CONSENT_REQUIRED') setConsentOpen(true)
      else setError(err.response?.data?.error || t.chat.sendFailed)
    }
    setLoading(false)
    inputRef.current?.focus()
  }

  const handleVoice = async (blob: Blob) => {
    setLoading(true)
    const form = new FormData()
    form.append('audio', blob, 'recording.webm')
    try {
      const { data } = await api.post('/api/chat/voice', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setMessages((m) => [...m, { role: 'PATIENT', content: data.transcript || '(voice)', id: Date.now() }])
      await showAssistantWithDelay(data)
    } catch {
      setError(t.chat.voiceFailed)
    }
    setLoading(false)
    inputRef.current?.focus()
  }

  const showSidebar = sidebarExpanded || session

  return (
    <AppLayout className={cn('h-screen overflow-hidden', crisisMode && 'crisis-mode')}>
      <ConsentModal open={consentOpen} onAccept={handleConsent} />
      <div className="flex flex-1 min-h-0 max-w-[1600px] w-full mx-auto overflow-hidden">
        <div
          className={cn(
            'flex flex-col min-w-0 flex-1 min-h-0 transition-colors duration-700',
            showSidebar ? 'md:w-[70%]' : 'w-full',
            crisisMode && 'bg-slate-900/95'
          )}
        >
          <div className="px-4 md:px-6 py-4 border-b flex justify-between items-center shrink-0 glass-panel rounded-none border-x-0 border-t-0">
            <div>
              <h2 className="font-semibold text-calm-900 dark:text-calm-100">{t.chat.title}</h2>
              {greeting && messages.length === 0 && (
                <p className="text-sm text-muted-foreground mt-0.5">{greeting}</p>
              )}
            </div>
            {risk && <RiskBadge level={risk.level} score={risk.score} />}
          </div>
          <MotivationalQuotesTicker crisisMode={crisisMode} />
          {crisisMode && (
            <Alert variant="crisis" className="mx-4 mt-3 rounded-lg border-0 shrink-0">
              {t.chat.crisisAlert}
            </Alert>
          )}
          {counselorActive && (
            <Alert className="mx-4 mt-3 shrink-0 border-emerald-200 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100">
              A counselor has joined the conversation. You are now speaking with a human counselor.
            </Alert>
          )}
          {error && <Alert className="mx-4 mt-3 shrink-0">{error}</Alert>}
          <ChatPanel
            messages={messages}
            assessmentOffer={lastOffer}
            typing={typing || loading}
            onLater={() => setLastOffer(null)}
            newMessageLabel={language === 'ur' ? '↓ Naye messages' : '↓ New messages'}
          />
          <div className="p-4 border-t flex gap-2 items-center shrink-0 bg-card/95 backdrop-blur-sm z-20">
            <VoiceRecorder onRecorded={handleVoice} disabled={loading || consentOpen} />
            <Input
              ref={inputRef}
              placeholder={t.chat.placeholder}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
              disabled={loading || consentOpen}
              className="flex-1"
              autoFocus
            />
            <Button size="icon" onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {showSidebar && <AssessmentSidebar />}
      </div>
    </AppLayout>
  )
}
