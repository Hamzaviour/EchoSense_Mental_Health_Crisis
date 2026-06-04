import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Loader2, MessageSquare, Search, UserCircle2, UserCheck } from 'lucide-react'
import CounselorLayout from '@/components/layout/CounselorLayout'
import ChatPanel, { ChatMessage } from '@/components/chat/ChatPanel'
import SuggestedResponsesPanel from '@/components/counselor/SuggestedResponsesPanel'
import RiskBadge from '@/components/RiskBadge'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import api from '@/api/client'
import { useCounselorSocket } from '@/hooks/useSocket'
import type { TriagePatient } from '@/types/counselor'

export default function ChatSupportView() {
  const [patients, setPatients] = useState<TriagePatient[]>([])
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<TriagePatient | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [counselorMsg, setCounselorMsg] = useState('')
  const [loadingList, setLoadingList] = useState(true)
  const [loadingChat, setLoadingChat] = useState(false)
  const [chatMode, setChatMode] = useState({ aiActive: true, counselorActive: false })
  const [takeoverBusy, setTakeoverBusy] = useState(false)
  const counselorInputRef = useRef<HTMLInputElement>(null)

  const loadPatients = useCallback(async () => {
    setLoadingList(true)
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      const { data } = await api.get('/api/counselor/triage-board', { params })
      const flat = Object.values(data.columns || {}).flat() as TriagePatient[]
      setPatients(flat)
      return flat
    } catch {
      setPatients([])
      return [] as TriagePatient[]
    } finally {
      setLoadingList(false)
    }
  }, [search])

  const loadMessages = useCallback(async (patient: TriagePatient) => {
    setLoadingChat(true)
    try {
      const { data } = await api.get(`/api/counselor/patients/${patient.id}`)
      setMessages(data.messages || [])
      setChatMode({
        aiActive: data.patient?.ai_active !== false,
        counselorActive: data.patient?.counselor_active === true,
      })
    } catch {
      setMessages([])
    } finally {
      setLoadingChat(false)
    }
  }, [])

  useCounselorSocket(() => {
    loadPatients()
    if (selected) loadMessages(selected)
  })

  useEffect(() => {
    loadPatients()
  }, [loadPatients])

  const sortedPatients = useMemo(
    () => [...patients].sort((a, b) => (b.latest_risk_score ?? 0) - (a.latest_risk_score ?? 0)),
    [patients]
  )

  const selectPatient = async (patient: TriagePatient) => {
    setSelected(patient)
    setCounselorMsg('')
    await loadMessages(patient)
  }

  const takeOverChat = async () => {
    if (!selected) return
    setTakeoverBusy(true)
    try {
      await api.post(`/api/counselor/patients/${selected.id}/takeover`)
      setChatMode({ aiActive: false, counselorActive: true })
      await loadMessages(selected)
      await loadPatients()
    } finally {
      setTakeoverBusy(false)
    }
  }

  const isHighRisk = selected && ['High', 'Critical'].includes(selected.latest_risk_level)

  const sendReply = async (text: string) => {
    if (!selected || !text.trim()) return
    await api.post('/api/counselor/messages', { patient_id: selected.id, content: text })
    await loadMessages(selected)
    await loadPatients()
    setCounselorMsg('')
    counselorInputRef.current?.focus()
  }

  return (
    <CounselorLayout>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: patient list */}
        <div className="w-80 shrink-0 border-r bg-card flex flex-col min-h-0">
          <div className="p-4 border-b shrink-0">
            <h2 className="text-lg font-semibold text-calm-900 dark:text-calm-100">Chat Support</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Live conversation · AI suggested responses
            </p>
            <div className="relative mt-3">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9 h-9"
                placeholder="Search patients..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          <ScrollArea className="flex-1 min-h-0">
            <div className="p-2 space-y-2">
              {loadingList && (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <span className="text-xs">Loading patients…</span>
                </div>
              )}
              {!loadingList && sortedPatients.length === 0 && (
                <p className="text-xs text-muted-foreground p-3 text-center">No patients found</p>
              )}
              {sortedPatients.map((patient) => (
                <button
                  key={patient.id}
                  type="button"
                  onClick={() => selectPatient(patient)}
                  className={cn(
                    'w-full text-left p-3 rounded-xl border transition-all',
                    selected?.id === patient.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  )}
                >
                  <div className="flex justify-between items-start gap-2 mb-1">
                    <span className="font-medium truncate">{patient.full_name}</span>
                    <RiskBadge level={patient.latest_risk_level} score={patient.latest_risk_score} />
                  </div>
                  <span className="text-xs text-muted-foreground font-mono block">{patient.patient_id}</span>
                  {patient.last_message?.content && (
                    <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                      {patient.last_message.content}
                    </p>
                  )}
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Right: chat + AI responses */}
        <div className="flex-1 flex flex-col min-h-0 min-w-0">
          {!selected ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-8">
              <UserCircle2 className="h-12 w-12 mb-3 opacity-30" />
              <p className="text-sm max-w-md">
                Select a patient to start live chat and use AI suggested responses.
              </p>
            </div>
          ) : (
            <>
              <div className="p-3 border-b shrink-0 flex flex-wrap items-center justify-between gap-2 bg-card">
                <div>
                  <h2 className="font-semibold capitalize">{selected.full_name}</h2>
                  <p className="text-xs text-muted-foreground font-mono">{selected.patient_id}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    <Badge variant={chatMode.aiActive ? 'secondary' : 'outline'} className="text-[10px]">
                      AI Active: {chatMode.aiActive ? 'ON' : 'OFF'}
                    </Badge>
                    <Badge variant={chatMode.counselorActive ? 'default' : 'outline'} className="text-[10px]">
                      Counselor Active: {chatMode.counselorActive ? 'ON' : 'OFF'}
                    </Badge>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <RiskBadge level={selected.latest_risk_level} score={selected.latest_risk_score} />
                  {isHighRisk && !chatMode.counselorActive && (
                    <Button size="sm" onClick={takeOverChat} disabled={takeoverBusy} className="gap-1">
                      <UserCheck className="h-3.5 w-3.5" />
                      {takeoverBusy ? 'Taking over…' : 'Take Over Chat'}
                    </Button>
                  )}
                </div>
              </div>
              <div className="flex flex-1 min-h-0 flex-col lg:flex-row">
              {/* Live chat — primary */}
              <div className="flex flex-col flex-1 min-h-0 lg:min-w-0 lg:border-r">
                <div className="px-3 py-2 border-b flex items-center gap-2 text-sm font-medium shrink-0 bg-card">
                  <MessageSquare className="h-4 w-4 text-primary" /> Live conversation
                </div>
                {loadingChat ? (
                  <div className="flex-1 flex items-center justify-center text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                    <span className="text-sm">Loading messages…</span>
                  </div>
                ) : (
                  <ChatPanel messages={messages} />
                )}
                <div className="p-3 border-t flex gap-2 shrink-0 bg-card/95 backdrop-blur-sm">
                  <Input
                    ref={counselorInputRef}
                    placeholder="Type a supportive reply..."
                    value={counselorMsg}
                    onChange={(e) => setCounselorMsg(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendReply(counselorMsg)}
                  />
                  <Button onClick={() => sendReply(counselorMsg)} disabled={!counselorMsg.trim()}>
                    Send
                  </Button>
                </div>
              </div>

              {/* AI suggested responses — side panel on desktop */}
              <div className="shrink-0 lg:w-[340px] xl:w-[380px] border-t lg:border-t-0 bg-muted/20 overflow-y-auto max-h-[45%] lg:max-h-none">
                <div className="p-3 sticky top-0 bg-muted/20 backdrop-blur-sm border-b lg:border-b-0 z-10">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    AI Assist
                  </p>
                </div>
                <div className="p-3">
                  <SuggestedResponsesPanel patientId={selected.id} onSend={sendReply} />
                </div>
              </div>
              </div>
            </>
          )}
        </div>
      </div>
    </CounselorLayout>
  )
}
