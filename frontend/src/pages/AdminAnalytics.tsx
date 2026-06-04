import { Fragment, useEffect, useState } from 'react'
import { Activity, Users, AlertTriangle, BarChart3, Radio, Trash2, UserPlus, TrendingUp, Grid3X3 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid,
} from 'recharts'
import CounselorLayout from '@/components/layout/CounselorLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert } from '@/components/ui/alert'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'
import api from '@/api/client'

const COLORS = ['#14b8a6', '#fbbf24', '#fb923c', '#64748b', '#6366f1']

interface AdminPatient {
  id: number
  patient_id: string
  full_name: string
  email?: string
  latest_risk_level: string
}

export default function AdminAnalytics() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [patients, setPatients] = useState<AdminPatient[]>([])
  const [adminMsg, setAdminMsg] = useState('')
  const [adminError, setAdminError] = useState('')
  const [tab, setTab] = useState<'overview' | 'heatmap'>('overview')
  const [counselorForm, setCounselorForm] = useState({
    full_name: '',
    email: '',
    password: '',
    specialization: '',
  })

  const loadAnalytics = () => api.get('/api/admin/analytics').then((res) => setData(res.data))
  const loadPatients = () => {
    if (!isAdmin) return
    api.get('/api/admin/patients').then((res) => setPatients(res.data.patients || [])).catch(() => {})
  }

  useEffect(() => {
    loadAnalytics()
    loadPatients()
  }, [isAdmin])

  const deletePatient = async (p: AdminPatient) => {
    if (!window.confirm(`Delete patient ${p.full_name} (${p.patient_id})? This cannot be undone.`)) return
    try {
      await api.delete(`/api/admin/patients/${p.id}`)
      setAdminMsg(`Patient ${p.patient_id} deleted.`)
      loadPatients()
      loadAnalytics()
    } catch {
      setAdminError('Failed to delete patient.')
    }
  }

  const addCounselor = async (e: React.FormEvent) => {
    e.preventDefault()
    setAdminError('')
    setAdminMsg('')
    try {
      await api.post('/api/admin/counselors', counselorForm)
      setAdminMsg(`Counselor ${counselorForm.full_name} created.`)
      setCounselorForm({ full_name: '', email: '', password: '', specialization: '' })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
      setAdminError(msg || 'Failed to create counselor.')
    }
  }

  if (!data) {
    return (
      <CounselorLayout>
        <div className="p-8 text-muted-foreground overflow-auto">Loading system metrics...</div>
      </CounselorLayout>
    )
  }

  const riskData = Object.entries((data.risk_distribution as Record<string, number>) || {}).map(([name, value]) => ({ name, value }))
  const sentimentData = Object.entries((data.sentiment_distribution as Record<string, number>) || {}).map(([name, value]) => ({ name, value }))

  const metrics = [
    { label: 'Total Patients', value: data.total_patients, icon: Users },
    { label: 'Escalations (30d)', value: data.escalations_30d, icon: AlertTriangle },
    { label: 'Resolution Rate', value: `${data.resolution_rate ?? 0}%`, icon: TrendingUp },
    { label: 'Escalations (7d)', value: data.escalation_count_7d ?? 0, icon: AlertTriangle },
  ]

  const DOW = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const heatCells = (data.heatmap_cells as { dow: number; hour: number; count: number; critical: number }[]) || []
  const maxHeat = Math.max(1, ...heatCells.map((c) => c.count))

  return (
    <CounselorLayout>
      <div className="p-6 space-y-6 max-w-7xl overflow-y-auto flex-1 min-h-0">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-calm-900 dark:text-calm-100">Analytics & Heatmap</h1>
            <p className="text-sm text-muted-foreground">Platform health · crisis trends · counselor workload</p>
          </div>
          <div className="flex gap-1 rounded-lg border p-1 bg-muted/30">
            <button type="button" onClick={() => setTab('overview')} className={cn('px-3 py-1.5 text-sm rounded-md', tab === 'overview' ? 'bg-card shadow-sm font-medium' : 'text-muted-foreground')}>
              Overview
            </button>
            <button type="button" onClick={() => setTab('heatmap')} className={cn('px-3 py-1.5 text-sm rounded-md flex items-center gap-1', tab === 'heatmap' ? 'bg-card shadow-sm font-medium' : 'text-muted-foreground')}>
              <Grid3X3 className="h-3.5 w-3.5" /> Heatmap
            </button>
          </div>
        </div>

        {adminMsg && <Alert>{adminMsg}</Alert>}
        {adminError && <Alert className="border-destructive/30 text-destructive">{adminError}</Alert>}

        {isAdmin && (
          <div className="grid lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Trash2 className="h-4 w-4" /> Manage Patients
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-64 overflow-y-auto">
                {patients.length === 0 && <p className="text-sm text-muted-foreground">No patients found.</p>}
                {patients.map((p) => (
                  <div key={p.id} className="flex items-center justify-between gap-2 rounded-lg border p-3 text-sm">
                    <div>
                      <p className="font-medium">{p.full_name}</p>
                      <p className="text-xs text-muted-foreground">{p.patient_id} · {p.email}</p>
                    </div>
                    <Button size="sm" variant="outline" className="text-destructive border-destructive/40 hover:bg-destructive/10" onClick={() => deletePatient(p)}>
                      Delete
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <UserPlus className="h-4 w-4" /> Add Counselor
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={addCounselor} className="space-y-3">
                  <div className="space-y-1">
                    <Label htmlFor="c-name">Full name</Label>
                    <Input id="c-name" value={counselorForm.full_name} onChange={(e) => setCounselorForm({ ...counselorForm, full_name: e.target.value })} required />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="c-email">Email</Label>
                    <Input id="c-email" type="email" value={counselorForm.email} onChange={(e) => setCounselorForm({ ...counselorForm, email: e.target.value })} required />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="c-pass">Password</Label>
                    <Input id="c-pass" type="password" value={counselorForm.password} onChange={(e) => setCounselorForm({ ...counselorForm, password: e.target.value })} required />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="c-spec">Specialization</Label>
                    <Input id="c-spec" value={counselorForm.specialization} onChange={(e) => setCounselorForm({ ...counselorForm, specialization: e.target.value })} placeholder="General Counseling" />
                  </div>
                  <Button type="submit" className="w-full">Create counselor account</Button>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map(({ label, value, icon: Icon }) => (
            <Card key={label} className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
                <Icon className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent><p className="text-2xl font-semibold">{String(value)}</p></CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Radio className="h-4 w-4" /> Kafka Stream Monitor
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Topics: patient_messages · sentiment_results · risk_analysis · counselor_notifications · emergency_alerts
            <br />
            <span className="text-xs">Enable Phase 2 docker-compose.full.yml for live stream processing</span>
          </CardContent>
        </Card>
        {tab === 'heatmap' && (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Daily crisis count (7d)</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={(data.daily_crisis_count as { date: string; count: number }[]) || []}>
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis width={28} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Weekly sentiment trend</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={(data.weekly_sentiment_trend as { date: string; avg_score: number }[]) || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} width={28} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="avg_score" stroke="#0d9488" strokeWidth={2} dot />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Counselor workload</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={(data.counselor_workload as { name: string; patients: number }[]) || []} layout="vertical">
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 9 }} />
                      <Tooltip />
                      <Bar dataKey="patients" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Grid3X3 className="h-4 w-4" /> Risk activity heatmap (day × hour)
                </CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <div className="inline-grid gap-1" style={{ gridTemplateColumns: '48px repeat(24, 28px)' }}>
                  <div />
                  {Array.from({ length: 24 }, (_, h) => (
                    <div key={h} className="text-[9px] text-center text-muted-foreground">{h}</div>
                  ))}
                  {DOW.map((day, dow) => (
                    <Fragment key={dow}>
                      <div className="text-xs text-muted-foreground flex items-center">{day}</div>
                      {Array.from({ length: 24 }, (_, hour) => {
                        const cell = heatCells.find((c) => c.dow === dow && c.hour === hour)
                        const intensity = cell ? cell.count / maxHeat : 0
                        return (
                          <div
                            key={`${dow}-${hour}`}
                            title={cell ? `${cell.count} events (${cell.critical} critical)` : '0'}
                            className="h-7 w-7 rounded-sm border border-border/40"
                            style={{ backgroundColor: intensity > 0 ? `rgba(239, 68, 68, ${0.15 + intensity * 0.85})` : undefined }}
                          />
                        )
                      })}
                    </Fragment>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}
        {tab === 'overview' && (
        <>
        <div className="grid lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle className="text-base">Risk distribution</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                    {riskData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-base">Sentiment distribution</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={sentimentData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0d9488" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
        <Card>
          <CardHeader><CardTitle className="text-base">Daily cases</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={(data.daily_cases as { date: string; count: number }[]) || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        </>
        )}
      </div>
    </CounselorLayout>
  )
}
