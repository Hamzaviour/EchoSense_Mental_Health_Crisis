import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Headphones, Volume2, VolumeX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import ToolTimer from './ToolTimer'

const GUIDED_LINES = [
  'Find a comfortable position. Let your shoulders soften.',
  'Notice your breath, without trying to change it.',
  'If thoughts arise, acknowledge them and let them pass like clouds.',
  'Bring attention to sounds around you, then back to your breath.',
  'Feel gratitude for this moment of rest you are giving yourself.',
  'When you are ready, gently open your eyes and return slowly.',
]

const DURATIONS = [
  { label: '3 min', seconds: 180 },
  { label: '5 min', seconds: 300 },
  { label: '10 min', seconds: 600 },
]

export default function MindfulnessSession() {
  const [duration, setDuration] = useState(DURATIONS[1].seconds)
  const [lineIdx, setLineIdx] = useState(0)
  const [speaking, setSpeaking] = useState(false)
  const [sessionActive, setSessionActive] = useState(false)
  const utterRef = useRef<SpeechSynthesisUtterance | null>(null)

  useEffect(() => {
    if (!sessionActive) return
    const interval = window.setInterval(() => {
      setLineIdx((i) => (i + 1) % GUIDED_LINES.length)
    }, Math.max(8000, (duration / GUIDED_LINES.length) * 1000))
    return () => window.clearInterval(interval)
  }, [sessionActive, duration])

  const speakLine = (text: string) => {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.rate = 0.85
    u.pitch = 1
    utterRef.current = u
    u.onend = () => setSpeaking(false)
    setSpeaking(true)
    window.speechSynthesis.speak(u)
  }

  const stopSpeech = () => {
    window.speechSynthesis.cancel()
    setSpeaking(false)
  }

  useEffect(() => () => stopSpeech(), [])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Headphones className="h-5 w-5 text-primary" />
          Mindfulness Session
        </CardTitle>
        <CardDescription>Guided calm with optional voice narration and timer</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-2 flex-wrap">
          {DURATIONS.map((d) => (
            <Button
              key={d.seconds}
              size="sm"
              variant={duration === d.seconds ? 'default' : 'outline'}
              onClick={() => setDuration(d.seconds)}
            >
              {d.label}
            </Button>
          ))}
        </div>

        <div className="relative flex h-40 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-calm-100 to-secondary/40">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute rounded-full bg-primary/10"
              animate={{
                scale: sessionActive ? [1, 1.8, 1] : 1,
                opacity: sessionActive ? [0.4, 0.15, 0.4] : 0.25,
              }}
              transition={{ duration: 4 + i, repeat: Infinity, ease: 'easeInOut', delay: i * 0.8 }}
              style={{ width: 80 + i * 40, height: 80 + i * 40 }}
            />
          ))}
          <motion.p
            key={lineIdx}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative z-10 max-w-sm px-6 text-center text-sm text-calm-900"
          >
            {GUIDED_LINES[lineIdx]}
          </motion.p>
        </div>

        <div className="flex flex-wrap gap-2 justify-center">
          <Button
            onClick={() => {
              setSessionActive(true)
              speakLine(GUIDED_LINES[lineIdx])
            }}
          >
            Start session
          </Button>
          <Button
            variant="outline"
            onClick={() => (speaking ? stopSpeech() : speakLine(GUIDED_LINES[lineIdx]))}
          >
            {speaking ? <VolumeX className="h-4 w-4 mr-1" /> : <Volume2 className="h-4 w-4 mr-1" />}
            {speaking ? 'Stop voice' : 'Read aloud'}
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setSessionActive(false)
              stopSpeech()
              setLineIdx(0)
            }}
          >
            Reset
          </Button>
        </div>

        <div className="rounded-xl border p-4">
          <ToolTimer
            totalSeconds={duration}
            label="Session timer"
            onComplete={() => {
              setSessionActive(false)
              stopSpeech()
            }}
          />
        </div>
      </CardContent>
    </Card>
  )
}
