import { useEffect, useState } from 'react'
import { BookOpen, Download, Loader2, Mic, Sparkles } from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import VoiceRecorder from '@/components/VoiceRecorder'
import api from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { useLanguage } from '@/context/LanguageContext'
import { cn } from '@/lib/utils'

type JournalEntry = {
  id: number
  entry_type: 'TEXT' | 'VOICE'
  content: string
  transcript?: string
  ai_summary?: string
  emotions: string[]
  coping_strategies: string[]
  created_at: string
}

export default function Journal() {
  const { t } = useLanguage()
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [content, setContent] = useState('')
  const [selected, setSelected] = useState<JournalEntry | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/api/patient/journal')
      const list = data.entries || []
      setEntries(list)
      if (list.length && !selected) setSelected(list[0])
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string; code?: string } } })?.response?.data
      if (msg?.code === 'CONSENT_REQUIRED') {
        setError(t.journal.consentRequired)
      } else {
        setError(msg?.error || t.journal.loadError)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const saveText = async () => {
    if (content.trim().length < 10) {
      setError(t.journal.minLength)
      return
    }
    setSaving(true)
    setError('')
    try {
      const { data } = await api.post('/api/patient/journal', { content: content.trim() })
      const entry = data.entry as JournalEntry
      setEntries((prev) => [entry, ...prev])
      setSelected(entry)
      setContent('')
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error
      setError(msg || t.journal.saveError)
    } finally {
      setSaving(false)
    }
  }

  const saveVoice = async (blob: Blob) => {
    setSaving(true)
    setError('')
    const form = new FormData()
    form.append('audio', blob, 'journal.webm')
    try {
      const { data } = await api.post('/api/patient/journal/voice', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const entry = data.entry as JournalEntry
      setEntries((prev) => [entry, ...prev])
      setSelected(entry)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error
      setError(msg || t.journal.voiceError)
    } finally {
      setSaving(false)
    }
  }

  const downloadPdf = async (entryId?: number) => {
    setExporting(true)
    setError('')
    try {
      const url = entryId
        ? `/api/patient/journal/export/pdf?entry_id=${entryId}`
        : '/api/patient/journal/export/pdf'
      const res = await api.get(url, { responseType: 'blob' })
      const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = entryId ? `journal_entry_${entryId}.pdf` : 'journal_export.pdf'
      a.click()
      window.URL.revokeObjectURL(blobUrl)
    } catch {
      setError(t.journal.exportError)
    } finally {
      setExporting(false)
    }
  }

  const active = selected

  return (
    <AppLayout>
      <div className="mx-auto max-w-6xl w-full flex-1 flex flex-col p-4 md:p-6 gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-calm-900 dark:text-calm-100 flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-primary" />
            {t.journal.title}
          </h1>
          <p className="text-muted-foreground mt-1">{t.journal.subtitle}</p>
        </div>

        {error && <Alert variant="crisis">{error}</Alert>}

        <div className="grid lg:grid-cols-2 gap-6 flex-1 min-h-0">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t.journal.writeTitle}</CardTitle>
                <CardDescription>{t.journal.writeDesc}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder={t.journal.placeholder}
                  rows={8}
                  className="w-full resize-y min-h-[160px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                <div className="flex flex-wrap items-center gap-2 justify-between">
                  <Button onClick={saveText} disabled={saving}>
                    {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    {t.journal.saveReflection}
                  </Button>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mic className="h-4 w-4" />
                    <span>{t.journal.voiceLabel}</span>
                    <VoiceRecorder onRecorded={saveVoice} disabled={saving} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2 flex flex-row items-center justify-between gap-2">
                <CardTitle className="text-sm">{t.journal.pastEntries}</CardTitle>
                {entries.length > 0 && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => downloadPdf()}
                    disabled={exporting}
                  >
                    {exporting ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      <Download className="h-3 w-3 mr-1" />
                    )}
                    {t.journal.exportPdf}
                  </Button>
                )}
              </CardHeader>
              <CardContent className="max-h-64 overflow-y-auto space-y-2">
                {loading && <p className="text-sm text-muted-foreground">{t.common.loading}</p>}
                {!loading && entries.length === 0 && (
                  <p className="text-sm text-muted-foreground">{t.journal.noEntries}</p>
                )}
                {entries.map((e) => (
                  <button
                    key={e.id}
                    type="button"
                    onClick={() => setSelected(e)}
                    className={cn(
                      'w-full text-left rounded-lg border p-3 text-sm transition-colors',
                      selected?.id === e.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-muted/50'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-[10px]">
                        {e.entry_type === 'VOICE' ? t.journal.voiceBadge : t.journal.textBadge}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">
                        {new Date(e.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-muted-foreground">{e.content}</p>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          <Card className="flex flex-col min-h-[320px]">
            <CardHeader className="flex flex-row items-start justify-between gap-2">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  {t.journal.aiInsights}
                </CardTitle>
                <CardDescription>{t.journal.aiInsightsDesc}</CardDescription>
              </div>
              {active && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => downloadPdf(active.id)}
                  disabled={exporting}
                >
                  {exporting ? (
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  ) : (
                    <Download className="h-3 w-3 mr-1" />
                  )}
                  {t.journal.exportEntryPdf}
                </Button>
              )}
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto space-y-4">
              {!active && (
                <p className="text-sm text-muted-foreground">{t.journal.selectOrSave}</p>
              )}
              {active && (
                <>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase mb-1">
                      {t.journal.summary}
                    </p>
                    <p className="text-sm leading-relaxed">{active.ai_summary || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase mb-2">
                      {t.journal.emotions}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {(active.emotions || []).map((em) => (
                        <Badge key={em} className="bg-violet-100 text-violet-900 dark:bg-violet-950 dark:text-violet-200">
                          {em}
                        </Badge>
                      ))}
                      {!active.emotions?.length && (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase mb-2">
                      {t.journal.copingStrategies}
                    </p>
                    <ul className="space-y-2">
                      {(active.coping_strategies || []).map((s, i) => (
                        <li key={i} className="text-sm flex gap-2">
                          <span className="text-primary font-medium">{i + 1}.</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="pt-2 border-t">
                    <p className="text-xs text-muted-foreground mb-1">{t.journal.fullEntry}</p>
                    <p className="text-sm whitespace-pre-wrap text-muted-foreground">{active.content}</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
