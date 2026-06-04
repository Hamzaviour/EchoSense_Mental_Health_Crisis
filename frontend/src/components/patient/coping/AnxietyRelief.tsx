import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import ToolTimer from './ToolTimer'

const STEPS = [
  { title: 'Pause', text: 'Stop what you are doing. Place both feet on the floor.' },
  { title: 'Breathe', text: 'Take 3 slow breaths — in for 4, out for 6.' },
  { title: 'Name it', text: 'Say quietly: "I am feeling anxious, and that is okay."' },
  { title: 'Release tension', text: 'Unclench jaw, drop shoulders, soften your hands.' },
  { title: 'One small action', text: 'Drink water, step outside, or text someone you trust.' },
]

export default function AnxietyRelief() {
  const [step, setStep] = useState(0)
  const [showTimer, setShowTimer] = useState(false)
  const done = step >= STEPS.length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Anxiety Relief Steps
        </CardTitle>
        <CardDescription>A guided sequence when anxiety feels overwhelming</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <AnimatePresence mode="wait">
          {!done ? (
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              className="space-y-2 min-h-[100px]"
            >
              <p className="text-xs uppercase tracking-wider text-primary">
                Step {step + 1} of {STEPS.length}
              </p>
              <p className="text-lg font-medium">{STEPS[step].title}</p>
              <p className="text-muted-foreground">{STEPS[step].text}</p>
            </motion.div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-4">
              <p className="font-medium text-calm-800">You took care of yourself. Well done.</p>
            </motion.div>
          )}
        </AnimatePresence>

        {!done && !showTimer && (
          <div className="flex gap-2">
            <Button onClick={() => setStep((s) => s + 1)}>
              {step < STEPS.length - 1 ? 'Next' : 'Finish'}
            </Button>
            <Button variant="outline" onClick={() => setShowTimer(true)}>Pause & breathe (60s)</Button>
          </div>
        )}

        {showTimer && (
          <div className="rounded-xl border p-4">
            <ToolTimer
              totalSeconds={60}
              label="Breathing pause"
              onComplete={() => {
                setShowTimer(false)
                setStep((s) => s + 1)
              }}
            />
          </div>
        )}

        {done && (
          <Button variant="outline" onClick={() => { setStep(0); setShowTimer(false) }}>
            Start again
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
