import { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2, Search, UserCircle2 } from 'lucide-react'
import CounselorLayout from '@/components/layout/CounselorLayout'
import CounselorDecisionPanel from '@/components/counselor/CounselorDecisionPanel'
import ClinicalReportPanel from '@/components/counselor/ClinicalReportPanel'
import RiskBadge from '@/components/RiskBadge'
import { Alert } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import api from '@/api/client'
import type { TriagePatient } from '@/types/counselor'

export default function DecisionWorkspaceView() {
  const [patients, setPatients] = useState<TriagePatient[]>([])
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<TriagePatient | null>(null)
  const [counselorNotes, setCounselorNotes] = useState('')
  const [loadingList, setLoadingList] = useState(true)
  const [escalationMsg, setEscalationMsg] = useState('')

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

  useEffect(() => {
    loadPatients()
  }, [loadPatients])

  const sortedPatients = useMemo(
    () => [...patients].sort((a, b) => (b.latest_risk_score ?? 0) - (a.latest_risk_score ?? 0)),
    [patients]
  )

  const selectPatient = async (patient: TriagePatient) => {
    setSelected(patient)
    setCounselorNotes('')
    setEscalationMsg('')
    try {
      const { data } = await api.get(`/api/counselor/patients/${patient.id}`)
      setCounselorNotes(data.patient?.counselor_notes || '')
    } catch {
      setCounselorNotes('')
    }
  }

  const refreshSelected = async () => {
    const flat = await loadPatients()
    if (!selected) return
    const updated = flat.find((p) => p.id === selected.id)
    if (updated) setSelected(updated)
    try {
      const { data } = await api.get(`/api/counselor/patients/${selected.id}`)
      setCounselorNotes(data.patient?.counselor_notes || '')
    } catch {
      /* keep existing notes */
    }
  }

  return (
    <CounselorLayout>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: patient list */}
        <div className="w-80 shrink-0 border-r bg-card flex flex-col min-h-0">
          <div className="p-4 border-b shrink-0">
            <h2 className="text-lg font-semibold text-calm-900 dark:text-calm-100">Decision Workspace</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Clinical decisions · reports · workflow actions
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
                  <span className="text-[10px] text-muted-foreground capitalize mt-1 block">
                    {patient.workflow_status?.replace(/_/g, ' ').toLowerCase() || 'new'}
                  </span>
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Right: decision + clinical report */}
        <div className="flex-1 min-h-0 overflow-y-auto p-6 md:p-8">
          {!selected && (
            <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground">
              <UserCircle2 className="h-12 w-12 mb-3 opacity-30" />
              <p className="text-sm max-w-md">
                Select a patient to manage workflow decisions and generate clinical case reports.
              </p>
            </div>
          )}

          {selected && (
            <div className="max-w-3xl mx-auto space-y-4">
              {escalationMsg && <Alert>{escalationMsg}</Alert>}

              <Card>
                <CardHeader className="pb-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle className="text-xl capitalize">{selected.full_name}</CardTitle>
                      <p className="text-sm font-mono text-muted-foreground mt-1">{selected.patient_id}</p>
                    </div>
                    <RiskBadge level={selected.latest_risk_level} score={selected.latest_risk_score} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                    <div className="rounded-lg border bg-muted/30 p-3">
                      <span className="text-xs text-muted-foreground block">Workflow</span>
                      <span className="font-medium capitalize">
                        {selected.workflow_status?.replace(/_/g, ' ').toLowerCase() || 'new'}
                      </span>
                    </div>
                    <div className="rounded-lg border bg-muted/30 p-3">
                      <span className="text-xs text-muted-foreground block">PHQ-9</span>
                      <span className="font-medium">{selected.assessment_status?.phq9_score ?? '—'}</span>
                    </div>
                    <div className="rounded-lg border bg-muted/30 p-3">
                      <span className="text-xs text-muted-foreground block">GAD-7</span>
                      <span className="font-medium">{selected.assessment_status?.gad7_score ?? '—'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <CounselorDecisionPanel
                patient={selected}
                onAction={refreshSelected}
                onEscalate={(r) => {
                  setEscalationMsg(`Escalation sent · Ref ${r.helpline_reference as string}`)
                  refreshSelected()
                }}
              />

              <ClinicalReportPanel
                patientId={selected.id}
                patientCode={selected.patient_id}
                counselorNotes={counselorNotes}
                onNotesChange={setCounselorNotes}
              />
            </div>
          )}
        </div>
      </div>
    </CounselorLayout>
  )
}
