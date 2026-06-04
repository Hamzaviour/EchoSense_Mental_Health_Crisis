import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

const STEPS = [
  { sense: '5 things you can SEE', prompt: 'Look around and name 5 things you can see right now.' },
  { sense: '4 things you can TOUCH', prompt: 'Notice 4 textures — your clothes, a surface, the air on your skin.' },
  { sense: '3 things you can HEAR', prompt: 'Listen for 3 distinct sounds, near or far.' },
  { sense: '2 things you can SMELL', prompt: 'Identify 2 scents, or imagine calming ones you enjoy.' },
  { sense: '1 thing you can TASTE', prompt: 'Notice one taste in your mouth, or sip water mindfully.' },
]

export default function GroundingExercise() {
  const [step, setStep] = useState(0)
  const done = step >= STEPS.length

  return (
    <Card>
      <CardHeader>
        <CardTitle>5-4-3-2-1 Grounding</CardTitle>
        <CardDescription>Bring attention to the present moment through your senses</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress value={done ? 100 : ((step + 1) / STEPS.length) * 100} />
        <AnimatePresence mode="wait">
          {!done ? (
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-3 min-h-[120px]"
            >
              <p className="text-sm font-medium text-primary">{STEPS[step].sense}</p>
              <p className="text-muted-foreground">{STEPS[step].prompt}</p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-6 space-y-2"
            >
              <p className="text-lg font-medium text-calm-800">You are here, in the present.</p>
              <p className="text-sm text-muted-foreground">Take a slow breath. You did well.</p>
            </motion.div>
          )}
        </AnimatePresence>
        <div className="flex gap-2">
          {!done ? (
            <>
              <Button onClick={() => setStep((s) => s + 1)}>Next step</Button>
              {step > 0 && (
                <Button variant="ghost" onClick={() => setStep((s) => s - 1)}>Back</Button>
              )}
            </>
          ) : (
            <Button variant="outline" onClick={() => setStep(0)}>Start again</Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
