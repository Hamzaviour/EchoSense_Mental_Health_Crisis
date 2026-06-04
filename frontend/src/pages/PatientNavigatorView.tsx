import { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2, Search, UserCircle2 } from 'lucide-react'
import CounselorLayout from '@/components/layout/CounselorLayout'
import RiskBadge from '@/components/RiskBadge'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import api from '@/api/client'
import type { CaseSummary } from '@/types/clinical'
import type { TriagePatient } from '@/types/counselor'

export default function PatientNavigatorView() {
  const [patients, setPatients] = useState<TriagePatient[]>([])
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<TriagePatient | null>(null)
  const [summary, setSummary] = useState<CaseSummary | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [error, setError] = useState('')

  const loadPatients = useCallback(async () => {
    setLoadingList(true)
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      const { data } = await api.get('/api/counselor/triage-board', { params })
      const flat = Object.values(data.columns || {}).flat() as TriagePatient[]
      setPatients(flat)
    } catch {
      setPatients([])
    } finally {
      setLoadingList(false)
    }
  }, [search])

  useEffect(() => {
    loadPatients()
  }, [loadPatients])

  const sortedPatients = useMemo(
    () => [...patients].sort((a, b) => (b.latest_risk_score ?? 0) - (a.latest_risk_score ?? 0)),
    [patients]
  )

  const selectPatient = async (patient: TriagePatient) => {
    setSelected(patient)
    setSummary(null)
    setError('')
    setLoadingSummary(true)
    try {
      const { data } = await api.get(`/api/counselor/patients/${patient.id}/case-summary`)
      setSummary(data)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error
      setError(msg || 'Could not load case summary. Try again or restart the backend.')
    } finally {
      setLoadingSummary(false)
    }
  }

  return (
    <CounselorLayout>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: patient list pane */}
        <div className="w-80 shrink-0 border-r bg-card flex flex-col min-h-0">
          <div className="p-4 border-b shrink-0">
            <h2 className="text-lg font-semibold text-calm-900 dark:text-calm-100">
              Patient Case Navigator
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              AI chat summary · select a patient
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
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Right: AI summary detail */}
        <div className="flex-1 min-h-0 overflow-y-auto p-6 md:p-8">
          {!selected && (
            <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground">
              <UserCircle2 className="h-12 w-12 mb-3 opacity-30" />
              <p className="text-sm max-w-md">
                Select a patient from the navigator to view their AI summary analysis.
              </p>
            </div>
          )}

          {selected && (
            <div className="max-w-3xl mx-auto space-y-6">
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle className="text-xl capitalize">{selected.full_name}</CardTitle>
                      <p className="text-sm font-mono text-muted-foreground mt-1">{selected.patient_id}</p>
                    </div>
                    <RiskBadge level={selected.latest_risk_level} score={selected.latest_risk_score} />
                  </div>
                </CardHeader>
                <CardContent>
                  {loadingSummary && (
                    <div className="flex items-center justify-center py-12 text-muted-foreground">
                      <Loader2 className="h-5 w-5 animate-spin mr-2" />
                      <span className="text-sm">Generating AI case summary…</span>
                    </div>
                  )}

                  {error && !loadingSummary && (
                    <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl p-4">
                      {error}
                    </p>
                  )}

                  {summary && !loadingSummary && (
                    <div className="space-y-5">
                      <div>
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                          Conversation Summary (AI Generated)
                        </h4>
                        <p className="text-sm leading-relaxed bg-muted/40 rounded-xl border p-4">
                          {summary.conversation_summary}
                        </p>
                      </div>

                      <div>
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                          AI Clinical Summary
                        </h4>
                        <p className="text-sm leading-relaxed bg-muted/40 rounded-xl border p-4">
                          {summary.ai_clinical_summary}
                        </p>
                      </div>

                      {Object.keys(summary.sentiment_distribution || {}).length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                            Sentiment Analysis
                          </h4>
                          <div className="flex flex-wrap gap-2 mb-2">
                            {Object.entries(summary.sentiment_distribution).map(([label, pct]) => (
                              <Badge key={label} variant="secondary">
                                {pct}% {label}
                              </Badge>
                            ))}
                          </div>
                          {summary.sentiment_trend && (
                            <p className="text-xs text-muted-foreground">{summary.sentiment_trend}</p>
                          )}
                        </div>
                      )}

                      {summary.trigger_keywords?.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                            Trigger Keywords
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {summary.trigger_keywords.map((kw) => (
                              <Badge key={kw} variant="outline">
                                {kw}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        <div className="rounded-lg border bg-muted/30 p-3">
                          <span className="text-xs text-muted-foreground block">PHQ-9</span>
                          <span className="font-semibold">{summary.assessments?.phq9?.score ?? '—'}</span>
                        </div>
                        <div className="rounded-lg border bg-muted/30 p-3">
                          <span className="text-xs text-muted-foreground block">GAD-7</span>
                          <span className="font-semibold">{summary.assessments?.gad7?.score ?? '—'}</span>
                        </div>
                        <div className="rounded-lg border bg-muted/30 p-3">
                          <span className="text-xs text-muted-foreground block">Escalation</span>
                          <span className="font-semibold text-sm">{summary.escalation_status ?? 'None'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </CounselorLayout>
  )
}
