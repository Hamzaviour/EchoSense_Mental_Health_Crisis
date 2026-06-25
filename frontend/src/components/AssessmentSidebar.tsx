import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, PanelRightClose } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { useAssessment } from '@/context/AssessmentContext'

const MIN_W = 280
const MAX_W = 420

export default function AssessmentSidebar() {
  const {
    session,
    sidebarExpanded,
    sidebarCollapsed,
    setSidebarExpanded,
    toggleCollapsed,
    saveAnswer,
    saving,
    startSelfAssessment,
  } = useAssessment()
  const [width, setWidth] = useState(320)
  const [selected, setSelected] = useState('')

  useEffect(() => setSelected(''), [session?.current_question?.id])

  if (!sidebarExpanded && !session) return null

  if (sidebarCollapsed && session) {
    return (
      <motion.aside
        initial={{ width: 0 }}
        animate={{ width: 52 }}
        className="border-l bg-card/50 flex flex-col items-center py-4 gap-2"
      >
        <Button variant="ghost" size="icon" onClick={() => { setSidebarExpanded(true); toggleCollapsed() }} title="Assessment Available">
          <ChevronRight className="h-4 w-4" />
        </Button>
        <span className="text-[10px] text-muted-foreground [writing-mode:vertical-rl] rotate-180">Assessment</span>
      </motion.aside>
    )
  }

  const q = session?.current_question
  const pct = session?.progress_percent ?? 0

  return (
    <motion.aside
      layout
      initial={{ width: 0, opacity: 0 }}
      animate={{ width, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 280, damping: 28 }}
      className="relative border-l bg-gradient-to-b from-calm-50/80 to-card flex flex-col shrink-0"
      style={{ minWidth: MIN_W, maxWidth: MAX_W }}
    >
      <div
        className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/20 z-10"
        onMouseDown={(e) => {
          e.preventDefault()
          const sx = e.clientX
          const sw = width
          const move = (ev: MouseEvent) => setWidth(Math.min(MAX_W, Math.max(MIN_W, sw - (ev.clientX - sx))))
          const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
          window.addEventListener('mousemove', move)
          window.addEventListener('mouseup', up)
        }}
      />
      <div className="p-4 flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-calm-800">Mental Health Assessment</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {session?.current_type_label} · {session?.type_progress}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={toggleCollapsed} className="shrink-0">
          <PanelRightClose className="h-4 w-4" />
        </Button>
      </div>
      <div className="px-4 pb-3">
        <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
          <span>{Math.round(pct)}% complete</span>
          <span>{session?.answered_count}/{session?.total_questions}</span>
        </div>
        <Progress value={pct} className="h-2" />
      </div>
      <Separator />
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          {session?.is_complete ? (
            <motion.div key="done" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="border-calm-200 bg-calm-50/50">
                <CardContent className="p-4 text-sm text-calm-900 space-y-3">
                  <p>
                    Thank you for sharing. Your responses help us support you better. You can continue chatting anytime.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-1"
                    onClick={() => startSelfAssessment()}
                  >
                    Start another assessment
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ) : q ? (
            <motion.div key={q.id} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }}>
              <Card className="shadow-sm">
                <CardContent className="p-4 space-y-4">
                  <p className="text-xs font-medium text-primary uppercase tracking-wide">Question {q.number}</p>
                  <p className="text-sm font-medium leading-relaxed">{q.text}</p>
                  <RadioGroup
                    value={selected}
                    onValueChange={(v) => {
                      setSelected(v)
                      saveAnswer(q.id, parseInt(v, 10))
                    }}
                    className="space-y-2"
                  >
                    {(q.options || []).map((opt: { value: number; label: string }) => (
                      <div
                        key={opt.value}
                        className={cn(
                          'flex items-center space-x-3 rounded-lg border p-3 transition-colors hover:bg-muted/50',
                          selected === String(opt.value) && 'border-primary bg-calm-50/50'
                        )}
                      >
                        <RadioGroupItem value={String(opt.value)} id={`q-${q.id}-${opt.value}`} disabled={saving} />
                        <Label htmlFor={`q-${q.id}-${opt.value}`} className="text-sm font-normal cursor-pointer flex-1">
                          {opt.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                  {saving && <p className="text-xs text-muted-foreground animate-pulse-soft">Saving...</p>}
                </CardContent>
              </Card>
            </motion.div>
          ) : (
            <p className="text-sm text-muted-foreground">Preparing your assessment...</p>
          )}
        </AnimatePresence>
      </div>
      <div className="p-3 border-t text-center">
        <p className="text-[11px] text-muted-foreground">Answers save automatically · collapse anytime</p>
      </div>
    </motion.aside>
  )
}
