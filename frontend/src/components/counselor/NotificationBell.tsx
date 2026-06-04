import { useCallback, useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import api from '@/api/client'
import { useCounselorSocket } from '@/hooks/useSocket'

type NotificationItem = {
  id: number
  title: string
  message: string
  notification_type: string
  type?: string
  is_read: boolean
  patient_id?: number
  patient_name?: string
  created_at: string
}

const TYPE_EMOJI: Record<string, string> = {
  CRITICAL_CASE: '🔴',
  PHQ_COMPLETED: '📋',
  COUNSELOR_MENTIONED: '💬',
  ESCALATION: '⚠️',
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unread, setUnread] = useState(0)
  const navigate = useNavigate()

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/api/counselor/notifications')
      setItems(data.notifications || [])
      setUnread(data.unread_count ?? (data.notifications || []).filter((n: NotificationItem) => !n.is_read).length)
    } catch {
      /* optional */
    }
  }, [])

  useCounselorSocket(() => {
    load()
  })

  useEffect(() => {
    load()
    const t = setInterval(load, 30000)
    return () => clearInterval(t)
  }, [load])

  const markRead = async (id: number) => {
    await api.patch(`/api/counselor/notifications/${id}/read`)
    load()
  }

  const markAllRead = async () => {
    const unreadItems = items.filter((n) => !n.is_read)
    await Promise.all(unreadItems.map((n) => api.patch(`/api/counselor/notifications/${n.id}/read`)))
    load()
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="relative h-9 w-9"
        aria-label="Notifications"
        onClick={() => setOpen((o) => !o)}
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 h-4 min-w-4 px-1 rounded-full bg-destructive text-destructive-foreground text-[10px] font-bold flex items-center justify-center">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </Button>

      {open && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40"
            aria-label="Close notifications"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 z-50 w-80 max-h-[70vh] overflow-hidden rounded-xl border bg-card shadow-xl">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <h3 className="font-semibold text-sm">Live Notifications</h3>
              {unread > 0 && (
                <button type="button" className="text-xs text-primary hover:underline" onClick={markAllRead}>
                  Mark all read
                </button>
              )}
            </div>
            <div className="overflow-y-auto max-h-[60vh]">
              {items.length === 0 && (
                <p className="text-sm text-muted-foreground p-4 text-center">No notifications yet</p>
              )}
              {items.map((n) => {
                const type = n.notification_type || n.type || 'ALERT'
                return (
                  <button
                    key={n.id}
                    type="button"
                    className={cn(
                      'w-full text-left px-4 py-3 border-b hover:bg-muted/50 transition-colors',
                      !n.is_read && 'bg-primary/5'
                    )}
                    onClick={() => {
                      markRead(n.id)
                      setOpen(false)
                      if (type === 'CRITICAL_CASE' || type === 'ESCALATION') navigate('/counselor/triage')
                      else if (type === 'PHQ_COMPLETED') navigate('/counselor/navigator')
                      else if (type === 'COUNSELOR_MENTIONED') navigate('/counselor/chat-support')
                    }}
                  >
                    <div className="flex gap-2 items-start">
                      <span className="text-base shrink-0">{TYPE_EMOJI[type] || '🔔'}</span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{n.title}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{n.message}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          {new Date(n.created_at).toLocaleString()}
                        </p>
                      </div>
                      {!n.is_read && <Badge variant="secondary" className="text-[10px] shrink-0">New</Badge>}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
