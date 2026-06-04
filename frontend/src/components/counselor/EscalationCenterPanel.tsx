import { useEffect, useState } from 'react'
import { Download, Phone, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import api from '@/api/client'

interface EscalationRow {
  id: number
  patient_id?: number
  patient_name?: string
  patient_code?: string
  risk_level: string
  risk_score: number
  status: string
  ai_summary?: string
  helpline_reference?: string
  helpline_forwarded?: boolean
  has_pdf?: boolean
  created_at: string
}

export default function EscalationCenterPanel({ refreshKey }: { refreshKey?: number }) {
  const [rows, setRows] = useState<EscalationRow[]>([])
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState<number | null>(null)

  const load = () => api.get('/api/counselor/escalations/active').then((r) => setRows(r.data.escalations || []))

  useEffect(() => { load() }, [refreshKey])

  const updateStatus = async (id: number, status: 'ACKNOWLEDGED' | 'RESOLVED') => {
    await api.patch(`/api/counselor/escalations/${id}/status`, { status })
    load()
  }

  const escalateHelpline = async (id: number) => {
    if (!window.confirm('Escalate this case to Umang helpline (0311-7786264)?')) return
    setBusy(id)
    setMsg('')
    try {
      const { data } = await api.post(`/api/counselor/escalations/${id}/helpline`)
      setMsg(`Helpline escalation sent · Ref ${data.helpline_reference as string}`)
      load()
    } catch {
      setMsg('Helpline escalation failed.')
    } finally {
      setBusy(null)
    }
  }

  const downloadPdf = async (id: number) => {
    const res = await api.get(`/api/escalations/${id}/pdf`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `escalation_${id}.pdf`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <Card className="mx-3 mt-2 border-destructive/30 shrink-0">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2 text-destructive">
          <ShieldAlert className="h-4 w-4" /> Crisis Escalation Center
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 max-h-52 overflow-y-auto">
        {msg && <Alert className="py-2 text-xs">{msg}</Alert>}
        {rows.length === 0 && (
          <p className="text-xs text-muted-foreground">No active critical escalations.</p>
        )}
        {rows.map((e) => (
          <div key={e.id} className="rounded-lg border p-3 text-sm space-y-2 bg-card">
            <div className="flex justify-between items-start gap-2">
              <div>
                <p className="font-medium">{e.patient_name}</p>
                <p className="text-xs text-muted-foreground">
                  {e.patient_code} · {e.risk_level} · Risk {e.risk_score?.toFixed?.(0) ?? e.risk_score}
                </p>
              </div>
              <Badge variant={e.risk_level === 'Critical' ? 'critical' : 'high'}>{e.status}</Badge>
            </div>
            {e.ai_summary && <p className="text-xs text-muted-foreground line-clamp-2">{e.ai_summary}</p>}
            {e.helpline_reference && (
              <p className="text-[10px] font-mono text-primary">Ref: {e.helpline_reference}</p>
            )}
            <div className="flex flex-wrap gap-1">
              {!e.helpline_forwarded && (
                <Button
                  size="sm"
                  variant="outline"
                  className="text-destructive border-destructive/50 hover:bg-destructive/10"
                  disabled={busy === e.id}
                  onClick={() => escalateHelpline(e.id)}
                >
                  <Phone className="h-3 w-3 mr-1" />
                  {busy === e.id ? 'Sending…' : 'Escalate to Helpline'}
                </Button>
              )}
              {e.has_pdf && (
                <Button size="sm" variant="outline" onClick={() => downloadPdf(e.id)}>
                  <Download className="h-3 w-3 mr-1" /> PDF
                </Button>
              )}
              {['SENT', 'OPEN'].includes(e.status) && (
                <Button size="sm" variant="outline" onClick={() => updateStatus(e.id, 'ACKNOWLEDGED')}>
                  Acknowledge
                </Button>
              )}
              {e.status !== 'RESOLVED' && (
                <Button size="sm" variant="calm" onClick={() => updateStatus(e.id, 'RESOLVED')}>
                  Mark resolved
                </Button>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
