import { useState, useEffect, useCallback } from 'react'
import { Search } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import CounselorLayout from '@/components/layout/CounselorLayout'
import TriageBoard from '@/components/counselor/TriageBoard'
import WorkQueueTabs from '@/components/counselor/WorkQueueTabs'
import EscalationCenterPanel from '@/components/counselor/EscalationCenterPanel'
import RiskBadge from '@/components/RiskBadge'
import SentimentBadge from '@/components/SentimentBadge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import api from '@/api/client'
import { useCounselorSocket } from '@/hooks/useSocket'
import type { TriagePatient, WorkflowTab } from '@/types/counselor'

export default function CounselorDashboard() {
  const [columns, setColumns] = useState<Record<string, TriagePatient[]>>({})
  const [workflowCounts, setWorkflowCounts] = useState<Record<string, number>>({})
  const [workflowTab, setWorkflowTab] = useState<WorkflowTab>('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<TriagePatient | null>(null)
  const [detail, setDetail] = useState<{
    sentiment_trend: { score: number; label: string; at: string }[]
    assessments: Record<string, { score?: number; severity?: string }>
  } | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const loadBoard = useCallback(async () => {
    const params: Record<string, string> = {}
    if (workflowTab) params.workflow = workflowTab
    if (search) params.search = search
    const { data } = await api.get('/api/counselor/triage-board', { params })
    setColumns(data.columns || {})
    setWorkflowCounts(data.workflow_counts || {})
  }, [workflowTab, search])

  useCounselorSocket(() => {
    loadBoard()
    if (selected) selectPatient(selected)
  })

  useEffect(() => {
    loadBoard()
    const t = setInterval(loadBoard, 20000)
    return () => clearInterval(t)
  }, [loadBoard])

  const selectPatient = async (p: TriagePatient) => {
    setSelected(p)
    const { data } = await api.get(`/api/counselor/patients/${p.id}`)
    setDetail(data)
  }

  const sentimentChart = detail?.sentiment_trend?.map((s) => ({
    time: s.at?.slice(11, 16),
    score: (s.score || 0) * 100,
  })) || []

  return (
    <CounselorLayout>
      <div className="flex flex-col flex-1 min-h-0 h-[calc(100vh-0px)] overflow-hidden">
        <div className="px-3 pt-3 pb-0 shrink-0 flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between border-b">
          <div>
            <h1 className="text-lg font-semibold text-calm-900 dark:text-calm-100">Live Triage Board</h1>
            <p className="text-xs text-muted-foreground">Real-time patient risk columns · clinical workflow</p>
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input className="pl-9 h-9" placeholder="Search patients..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>

        <WorkQueueTabs active={workflowTab} counts={workflowCounts} onChange={setWorkflowTab} />

        <EscalationCenterPanel refreshKey={refreshKey} />

        <div className="flex flex-1 min-h-0 overflow-hidden flex-col lg:flex-row">
          <div className="lg:w-[55%] xl:w-[60%] flex flex-col min-h-0 border-r overflow-hidden">
            <TriageBoard columns={columns} selectedId={selected?.id} onSelect={selectPatient} />
          </div>

          <div className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
            {selected && detail ? (
              <>
                <div className="p-3 border-b shrink-0 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="font-semibold">{selected.full_name}</h2>
                    <p className="text-xs text-muted-foreground">{selected.patient_id}</p>
                  </div>
                  <RiskBadge level={selected.latest_risk_level} score={selected.latest_risk_score} />
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
                  <div className="grid grid-cols-3 gap-2">
                    <Card><CardHeader className="p-2 pb-0"><CardTitle className="text-[10px] text-muted-foreground">PHQ-9</CardTitle></CardHeader>
                      <CardContent className="p-2 pt-0 text-sm">{detail.assessments?.phq9?.score ?? '—'}</CardContent></Card>
                    <Card><CardHeader className="p-2 pb-0"><CardTitle className="text-[10px] text-muted-foreground">GAD-7</CardTitle></CardHeader>
                      <CardContent className="p-2 pt-0 text-sm">{detail.assessments?.gad7?.score ?? '—'}</CardContent></Card>
                    <Card><CardHeader className="p-2 pb-0"><CardTitle className="text-[10px] text-muted-foreground">Sentiment</CardTitle></CardHeader>
                      <CardContent className="p-2 pt-1">
                        {selected.sentiment_label || selected.sentiment_score != null ? (
                          <SentimentBadge
                            label={selected.sentiment_label}
                            score={selected.sentiment_score}
                            className="text-xs"
                          />
                        ) : (
                          <span className="text-sm text-muted-foreground">—</span>
                        )}
                      </CardContent></Card>
                  </div>

                  <Card>
                    <CardHeader className="pb-0 flex flex-row items-center justify-between">
                      <CardTitle className="text-xs">Sentiment trend</CardTitle>
                      {detail.sentiment_trend?.[detail.sentiment_trend.length - 1]?.label && (
                        <SentimentBadge
                          label={detail.sentiment_trend[detail.sentiment_trend.length - 1].label}
                          score={detail.sentiment_trend[detail.sentiment_trend.length - 1].score}
                          className="text-[10px] py-0 h-5"
                        />
                      )}
                    </CardHeader>
                    <CardContent className="p-2 space-y-2">
                      <ResponsiveContainer width="100%" height={140}>
                        <LineChart data={sentimentChart}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="time" tick={{ fontSize: 9 }} />
                          <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} width={28} />
                          <Tooltip />
                          <Line type="monotone" dataKey="score" stroke="#0d9488" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                      {detail.sentiment_trend && detail.sentiment_trend.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1 border-t">
                          {detail.sentiment_trend.slice(-8).map((s, i) => (
                            <SentimentBadge
                              key={`${s.at}-${i}`}
                              label={s.label}
                              score={s.score}
                              showScore={false}
                              className="text-[9px] py-0 h-4 px-1.5"
                            />
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm p-8 text-center">
                Select a patient from the triage board to view risk overview and sentiment trend
              </div>
            )}
          </div>
        </div>
      </div>
    </CounselorLayout>
  )
}
