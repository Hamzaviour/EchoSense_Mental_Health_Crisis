import { useState } from 'react'
import { Moon, Check } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import ToolTimer from './ToolTimer'
import { cn } from '@/lib/utils'

const TIPS = [
  'Keep your bedroom cool, dark, and quiet',
  'Avoid caffeine after 2 PM',
  'Put screens away 30 minutes before bed',
  'Write tomorrow\'s worries on paper to release them',
  'Try the same calming routine each night',
]

export default function SleepGuidance() {
  const [checked, setChecked] = useState<Set<number>>(new Set())

  const toggle = (i: number) => {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Moon className="h-5 w-5 text-primary" />
          Sleep Guidance
        </CardTitle>
        <CardDescription>Wind-down checklist and a gentle bedtime timer</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <ul className="space-y-2">
          {TIPS.map((tip, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => toggle(i)}
                className={cn(
                  'flex w-full items-start gap-3 rounded-lg border p-3 text-left text-sm transition-colors',
                  checked.has(i) ? 'border-primary/40 bg-primary/5' : 'hover:bg-muted/50'
                )}
              >
                <span
                  className={cn(
                    'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border',
                    checked.has(i) && 'bg-primary border-primary text-primary-foreground'
                  )}
                >
                  {checked.has(i) && <Check className="h-3 w-3" />}
                </span>
                {tip}
              </button>
            </li>
          ))}
        </ul>
        <div className="rounded-xl border bg-calm-50/50 p-4">
          <ToolTimer totalSeconds={300} label="Wind-down timer (5 minutes)" />
        </div>
      </CardContent>
    </Card>
  )
}
