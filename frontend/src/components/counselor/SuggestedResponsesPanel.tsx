import { useState } from 'react'
import { RefreshCw, Sparkles, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import api from '@/api/client'

const TONES = [
  { key: 'calm', label: 'Calm' },
  { key: 'supportive', label: 'Supportive' },
  { key: 'firm', label: 'Firm' },
] as const

export default function SuggestedResponsesPanel({
  patientId,
  onSend,
}: {
  patientId: number
  onSend: (text: string) => void
}) {
  const [tone, setTone] = useState<'calm' | 'supportive' | 'firm'>('supportive')
  const [responses, setResponses] = useState<string[]>([])
  const [edited, setEdited] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(false)

  const load = async (t = tone) => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/counselor/suggested-responses', { patient_id: patientId, tone: t })
      setResponses(data.responses || [])
      setEdited({})
    } finally {
      setLoading(false)
    }
  }

  const getText = (i: number) => edited[i] ?? responses[i] ?? ''

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" /> AI Suggested Responses
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1">
          {TONES.map((t) => (
            <Button
              key={t.key}
              size="sm"
              variant={tone === t.key ? 'default' : 'outline'}
              onClick={() => { setTone(t.key); load(t.key) }}
            >
              {t.label}
            </Button>
          ))}
          <Button size="sm" variant="ghost" onClick={() => load()} disabled={loading}>
            <RefreshCw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
          </Button>
        </div>
        {responses.length === 0 && !loading && (
          <Button size="sm" variant="outline" onClick={() => load()} className="w-full">
            Generate safe responses
          </Button>
        )}
        {responses.map((_, i) => (
          <div key={i} className="space-y-1">
            <Input
              value={getText(i)}
              onChange={(e) => setEdited({ ...edited, [i]: e.target.value })}
              className="text-sm"
            />
            <Button size="sm" variant="calm" className="w-full gap-1" onClick={() => onSend(getText(i))}>
              <Send className="h-3 w-3" /> Send response {i + 1}
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
