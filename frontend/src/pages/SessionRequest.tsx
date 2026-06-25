import { useEffect, useState } from 'react'
import { CalendarClock, MessageSquare, Phone, UserRound } from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import api from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { useLanguage } from '@/context/LanguageContext'
import { cn } from '@/lib/utils'

type Counselor = {
  id: number
  counselor_id: string
  full_name: string
  specialization: string
  is_on_duty: boolean
}

type SessionReq = {
  id: number
  request_type: 'CALLBACK' | 'CHAT_SESSION'
  status: string
  message?: string
  preferred_contact?: string
  counselor_id?: number
  counselor_name?: string
  created_at: string
}

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200',
  APPROVED: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200',
  DECLINED: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200',
  COMPLETED: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200',
}

export default function SessionRequestPage() {
  const { t } = useLanguage()
  const [counselors, setCounselors] = useState<Counselor[]>([])
  const [requests, setRequests] = useState<SessionReq[]>([])
  const [counselorId, setCounselorId] = useState<string>('')
  const [requestType, setRequestType] = useState<'CALLBACK' | 'CHAT_SESSION'>('CHAT_SESSION')
  const [message, setMessage] = useState('')
  const [contact, setContact] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const [cRes, rRes] = await Promise.all([
        api.get('/api/patient/counselors'),
        api.get('/api/patient/session-requests'),
      ])
      setCounselors(cRes.data.counselors || [])
      setRequests(rRes.data.requests || [])
    } catch {
      setError(t.sessionRequest.loadError)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async () => {
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      const { data } = await api.post('/api/patient/session-requests', {
        counselor_id: counselorId ? Number(counselorId) : undefined,
        request_type: requestType,
        message: message.trim() || undefined,
        preferred_contact: contact.trim() || undefined,
      })
      setRequests((prev) => [data.request, ...prev])
      setSuccess(t.sessionRequest.success)
      setMessage('')
    } catch (e: unknown) {
      const res = (e as { response?: { data?: { error?: string } } })?.response?.data
      setError(res?.error || t.sessionRequest.submitError)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl w-full flex-1 flex flex-col p-4 md:p-6 gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-calm-900 dark:text-calm-100 flex items-center gap-2">
            <CalendarClock className="h-6 w-6 text-primary" />
            {t.sessionRequest.title}
          </h1>
          <p className="text-muted-foreground mt-1">{t.sessionRequest.subtitle}</p>
        </div>

        {error && <Alert variant="crisis">{error}</Alert>}
        {success && <Alert>{success}</Alert>}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.sessionRequest.formTitle}</CardTitle>
            <CardDescription>{t.sessionRequest.formDesc}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium flex items-center gap-2 mb-2">
                <UserRound className="h-4 w-4" />
                {t.sessionRequest.chooseCounselor}
              </label>
              <select
                value={counselorId}
                onChange={(e) => setCounselorId(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">{t.sessionRequest.anyCounselor}</option>
                {counselors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name} — {c.specialization}
                    {!c.is_on_duty ? ` (${t.sessionRequest.offDuty})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <p className="text-sm font-medium mb-2">{t.sessionRequest.requestType}</p>
              <div className="grid sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRequestType('CHAT_SESSION')}
                  className={cn(
                    'rounded-lg border p-4 text-left transition-colors',
                    requestType === 'CHAT_SESSION'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  )}
                >
                  <MessageSquare className="h-5 w-5 text-primary mb-2" />
                  <p className="font-medium text-sm">{t.sessionRequest.chatSession}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t.sessionRequest.chatDesc}</p>
                </button>
                <button
                  type="button"
                  onClick={() => setRequestType('CALLBACK')}
                  className={cn(
                    'rounded-lg border p-4 text-left transition-colors',
                    requestType === 'CALLBACK'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  )}
                >
                  <Phone className="h-5 w-5 text-primary mb-2" />
                  <p className="font-medium text-sm">{t.sessionRequest.callback}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t.sessionRequest.callbackDesc}</p>
                </button>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">{t.sessionRequest.contact}</label>
              <Input
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                placeholder={t.sessionRequest.contactPlaceholder}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">{t.sessionRequest.messageOptional}</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                placeholder={t.sessionRequest.messagePlaceholder}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            <Button onClick={submit} disabled={submitting} className="w-full sm:w-auto">
              {submitting ? t.sessionRequest.submitting : t.sessionRequest.submit}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t.sessionRequest.history}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading && <p className="text-sm text-muted-foreground">{t.common.loading}</p>}
            {!loading && requests.length === 0 && (
              <p className="text-sm text-muted-foreground">{t.sessionRequest.noRequests}</p>
            )}
            {requests.map((r) => (
              <div key={r.id} className="rounded-lg border p-3 text-sm space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className={STATUS_COLORS[r.status] || ''}>{r.status}</Badge>
                  <Badge variant="outline">
                    {r.request_type === 'CALLBACK'
                      ? t.sessionRequest.callback
                      : t.sessionRequest.chatSession}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground ml-auto">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
                {r.counselor_name && (
                  <p className="text-muted-foreground">
                    {t.sessionRequest.counselor}: {r.counselor_name}
                  </p>
                )}
                {r.message && <p>{r.message}</p>}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
