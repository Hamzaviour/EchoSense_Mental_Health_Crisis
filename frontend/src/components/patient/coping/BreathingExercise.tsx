import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

const PHASES = [
  { label: 'Breathe in', seconds: 4, scale: 1.35 },
  { label: 'Hold', seconds: 4, scale: 1.35 },
  { label: 'Breathe out', seconds: 4, scale: 0.85 },
  { label: 'Hold', seconds: 4, scale: 0.85 },
]

export default function BreathingExercise() {
  const [active, setActive] = useState(false)
  const [phaseIdx, setPhaseIdx] = useState(0)
  const [countdown, setCountdown] = useState(PHASES[0].seconds)
  const [cycles, setCycles] = useState(0)

  useEffect(() => {
    if (!active) return
    const id = window.setInterval(() => {
      setCountdown((c) => {
        if (c > 1) return c - 1
        setPhaseIdx((i) => {
          const next = (i + 1) % PHASES.length
          if (next === 0) setCycles((cy) => cy + 1)
          setCountdown(PHASES[next].seconds)
          return next
        })
        return PHASES[(phaseIdx + 1) % PHASES.length].seconds
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [active, phaseIdx])

  const phase = PHASES[phaseIdx]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Box Breathing</CardTitle>
        <CardDescription>4-4-4-4 rhythm to calm your nervous system</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-6">
        <div className="relative flex h-48 w-48 items-center justify-center">
          <motion.div
            animate={{
              scale: active ? phase.scale : 1,
              opacity: active ? 0.9 : 0.6,
            }}
            transition={{ duration: phase.seconds, ease: 'easeInOut' }}
            className={cn(
              'absolute inset-4 rounded-full bg-gradient-to-br from-calm-200 to-primary/30',
              active && 'shadow-lg shadow-primary/20'
            )}
          />
          <div className="relative z-10 text-center">
            <p className="text-lg font-medium text-calm-900">{active ? phase.label : 'Ready'}</p>
            <p className="text-4xl font-mono tabular-nums text-calm-700 mt-1">
              {active ? countdown : '—'}
            </p>
          </div>
        </div>
        {active && (
          <p className="text-sm text-muted-foreground">Cycle {cycles + 1} · 4 cycles recommended</p>
        )}
        <Button
          onClick={() => {
            if (active) {
              setActive(false)
              setPhaseIdx(0)
              setCountdown(PHASES[0].seconds)
              setCycles(0)
            } else {
              setActive(true)
            }
          }}
        >
          {active ? 'Stop' : 'Begin exercise'}
        </Button>
      </CardContent>
    </Card>
  )
}
