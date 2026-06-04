import { useState } from 'react'
import {
  AlertTriangle, Calendar, CheckCircle, MessageSquare, Phone, UserCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import api from '@/api/client'
import type { TriagePatient } from '@/types/counselor'

export default function CounselorDecisionPanel({
  patient,
  onAction,
  onEscalate,
}: {
  patient: TriagePatient
  onAction: () => void
  onEscalate: (result: Record<string, unknown>) => void
}) {
  const [followUpDate, setFollowUpDate] = useState('')
  const [sessionDate, setSessionDate] = useState('')
  const [busy, setBusy] = useState('')

  const patch = async (body: Record<string, unknown>) => {
    setBusy(body.workflow_status as string || 'action')
    try {
      await api.patch(`/api/counselor/patients/${patient.id}/workflow`, body)
      onAction()
    } finally {
      setBusy('')
    }
  }

  const escalate = async () => {
    if (!window.confirm(`Escalate ${patient.full_name} to Umang helpline?`)) return
    setBusy('escalate')
    try {
      const { data } = await api.post('/api/counselor/escalate', { patient_id: patient.id })
      onEscalate(data)
      onAction()
    } finally {
      setBusy('')
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Decision Panel</CardTitle>
      </CardHeader>
      <CardContent className="grid sm:grid-cols-2 gap-2">
        <Button size="sm" variant="outline" className="justify-start gap-2" disabled={!!busy}
          onClick={() => patch({ workflow_status: 'IN_PROGRESS', assign_to_me: true })}>
          <MessageSquare className="h-3.5 w-3.5" /> Take case (In Progress)
        </Button>
        <Button size="sm" variant="outline" className="justify-start gap-2" disabled={!!busy}
          onClick={() => patch({ workflow_status: 'RESOLVED' })}>
          <CheckCircle className="h-3.5 w-3.5" /> Mark resolved
        </Button>
        <div className="sm:col-span-2 space-y-1">
          <Label className="text-xs">Assign follow-up</Label>
          <div className="flex gap-2">
            <Input type="datetime-local" value={followUpDate} onChange={(e) => setFollowUpDate(e.target.value)} className="text-xs" />
            <Button size="sm" disabled={!followUpDate || !!busy}
              onClick={() => patch({ follow_up_at: new Date(followUpDate).toISOString() })}>
              <UserCheck className="h-3.5 w-3.5 mr-1" /> Assign
            </Button>
          </div>
        </div>
        <div className="sm:col-span-2 space-y-1">
          <Label className="text-xs">Schedule session</Label>
          <div className="flex gap-2">
            <Input type="datetime-local" value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} className="text-xs" />
            <Button size="sm" disabled={!sessionDate || !!busy}
              onClick={() => patch({ session_scheduled_at: new Date(sessionDate).toISOString(), workflow_status: 'IN_PROGRESS' })}>
              <Calendar className="h-3.5 w-3.5 mr-1" /> Schedule
            </Button>
          </div>
        </div>
        {(patient.latest_risk_level === 'Critical' || patient.latest_risk_level === 'High') && (
          <Button size="sm" variant="outline"
            className="sm:col-span-2 justify-start gap-2 text-destructive border-destructive/40 hover:bg-destructive/10"
            disabled={!!busy} onClick={escalate}>
            <AlertTriangle className="h-3.5 w-3.5" />
            {busy === 'escalate' ? 'Escalating...' : 'Escalate to Umang Helpline'}
          </Button>
        )}
        {patient.escalation_id && (
          <p className="sm:col-span-2 text-xs text-muted-foreground flex items-center gap-1">
            <Phone className="h-3 w-3" /> Escalation status: {patient.escalation_status}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
