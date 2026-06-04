import { useEffect, useRef, useState } from 'react'
import { Pause, Play, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

type ToolTimerProps = {
  totalSeconds: number
  label?: string
  onComplete?: () => void
  className?: string
}

export default function ToolTimer({ totalSeconds, label, onComplete, className }: ToolTimerProps) {
  const [remaining, setRemaining] = useState(totalSeconds)
  const [running, setRunning] = useState(false)
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  useEffect(() => {
    setRemaining(totalSeconds)
    setRunning(false)
  }, [totalSeconds])

  useEffect(() => {
    if (!running || remaining <= 0) return
    const id = window.setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          setRunning(false)
          onCompleteRef.current?.()
          return 0
        }
        return r - 1
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [running, remaining])

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  const progress = ((totalSeconds - remaining) / totalSeconds) * 100

  return (
    <div className={cn('space-y-3', className)}>
      {label && <p className="text-sm text-muted-foreground">{label}</p>}
      <div className="text-3xl font-mono tabular-nums text-center text-calm-800">
        {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
      </div>
      <Progress value={progress} className="h-2" />
      <div className="flex justify-center gap-2">
        <Button size="sm" variant="outline" onClick={() => setRunning((r) => !r)} disabled={remaining === 0}>
          {running ? <Pause className="h-4 w-4 mr-1" /> : <Play className="h-4 w-4 mr-1" />}
          {running ? 'Pause' : 'Start'}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            setRunning(false)
            setRemaining(totalSeconds)
          }}
        >
          <RotateCcw className="h-4 w-4 mr-1" />
          Reset
        </Button>
      </div>
    </div>
  )
}
