import { useState, useRef } from 'react'
import { Mic, Square, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function VoiceRecorder({
  onRecorded,
  disabled,
}: {
  onRecorded: (blob: Blob) => Promise<void>
  disabled?: boolean
}) {
  const [recording, setRecording] = useState(false)
  const [uploading, setUploading] = useState(false)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach((t) => t.stop())
        setUploading(true)
        await onRecorded(blob)
        setUploading(false)
      }
      mediaRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch {
      alert('Microphone access is needed for voice messages.')
    }
  }

  const stop = () => {
    mediaRef.current?.stop()
    setRecording(false)
  }

  if (uploading) return <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />

  return (
    <Button
      type="button"
      variant={recording ? 'secondary' : 'ghost'}
      size="icon"
      onClick={recording ? stop : start}
      disabled={disabled}
      className={recording ? 'text-destructive' : 'text-primary'}
    >
      {recording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
    </Button>
  )
}
