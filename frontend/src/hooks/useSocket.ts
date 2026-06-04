import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import type { ChatMessage } from '@/components/chat/ChatPanel'

const SOCKET_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : '')

export function useCounselorSocket(onUpdate: (payload: Record<string, unknown>) => void) {
  const cbRef = useRef(onUpdate)
  cbRef.current = onUpdate

  useEffect(() => {
    let socket: Socket
    try {
      socket = io(SOCKET_URL, { transports: ['websocket', 'polling'] })
      socket.on('connect', () => socket.emit('join_counselors'))
      socket.on('patient_live_update', (p) => cbRef.current?.(p))
      socket.on('counselor_alert', (p) => cbRef.current?.({ ...p, event: 'counselor_alert' }))
      socket.on('queue_update', () => cbRef.current?.({ event: 'queue_update' }))
    } catch { /* socket optional */ }
    return () => { socket?.disconnect() }
  }, [])
}

export function usePatientSocket(
  patientDbId: number | null | undefined,
  onCounselorMessage: (msg: ChatMessage) => void,
  onTakeover?: (msg: ChatMessage) => void
) {
  const cbRef = useRef(onCounselorMessage)
  const takeoverRef = useRef(onTakeover)
  cbRef.current = onCounselorMessage
  takeoverRef.current = onTakeover

  useEffect(() => {
    if (!patientDbId) return
    let socket: Socket
    try {
      socket = io(SOCKET_URL, { transports: ['websocket', 'polling'] })
      socket.on('connect', () => {
        socket.emit('join_patient', { patient_id: patientDbId })
      })
      socket.on('counselor_message', (payload: ChatMessage) => {
        cbRef.current?.({
          id: payload.id,
          role: payload.role || 'COUNSELOR',
          content: payload.content,
        })
      })
      socket.on('counselor_takeover', (payload: ChatMessage) => {
        const msg = {
          id: payload.id,
          role: 'SYSTEM',
          content: payload.content,
        }
        takeoverRef.current?.(msg)
        cbRef.current?.(msg)
      })
    } catch { /* socket optional */ }
    return () => { socket?.disconnect() }
  }, [patientDbId])
}
