import { useCallback, useEffect, useState } from 'react'
import { CalendarClock, Check, X } from 'lucide-react'
import api from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

type SessionReq = {
  id: number
  patient_name?: string
  patient_code?: string
  request_type: string
  status: string
  message?: string
  preferred_contact?: string
  created_at: string
}

export default function SessionRequestsPanel() {
  const [requests, setRequests] = useState<SessionReq[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/api/counselor/session-requests', { params: { status: 'PENDING' } })
      setRequests(data.requests || [])
    } catch {
      setRequests([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const updateStatus = async (id: number, status: 'APPROVED' | 'DECLINED') => {
    await api.patch(`/api/counselor/session-requests/${id}`, { status })
    load()
  }

  return (
    <Card>
      <CardHeader className="py-3 px-4 flex flex-row items-center gap-2">
        <CalendarClock className="h-4 w-4 text-primary" />
        <CardTitle className="text-sm">Session requests</CardTitle>
        {requests.length > 0 && (
          <Badge variant="secondary" className="ml-auto text-[10px]">
            {requests.length} pending
          </Badge>
        )}
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-2 max-h-48 overflow-y-auto">
        {loading && <p className="text-xs text-muted-foreground">Loading...</p>}
        {!loading && requests.length === 0 && (
          <p className="text-xs text-muted-foreground">No pending session requests.</p>
        )}
        {requests.map((r) => (
          <div key={r.id} className="rounded-lg border p-2 text-xs space-y-1">
            <p className="font-medium">
              {r.patient_name} ({r.patient_code})
            </p>
            <p className="text-muted-foreground">
              {r.request_type === 'CALLBACK' ? 'Callback' : 'Chat session'}
              {r.preferred_contact ? ` · ${r.preferred_contact}` : ''}
            </p>
            {r.message && <p className="line-clamp-2">{r.message}</p>}
            <div className="flex gap-1 pt-1">
              <Button size="sm" variant="outline" className="h-7 text-[10px]" onClick={() => updateStatus(r.id, 'APPROVED')}>
                <Check className="h-3 w-3 mr-1" />
                Approve
              </Button>
              <Button size="sm" variant="ghost" className="h-7 text-[10px]" onClick={() => updateStatus(r.id, 'DECLINED')}>
                <X className="h-3 w-3 mr-1" />
                Decline
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
