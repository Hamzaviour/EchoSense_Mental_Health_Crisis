import { useEffect, useState } from 'react'
import { CheckCircle2, Download, RefreshCw, Sparkles, Target, ListChecks, Lightbulb } from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import api from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { useLanguage } from '@/context/LanguageContext'
import { cn } from '@/lib/utils'

const FOCUS_CHIPS = ['Sleep', 'Anxiety', 'Stress', 'Motivation', 'Low mood']

type TherapyPlan = {
  id: number
  weekly_goals: string[]
  coping_tasks: string[]
  behavioral_suggestions: string[]
  summary: string
  created_at: string
  has_pdf: boolean
}

export default function TherapyPlanPage() {
  const { t } = useLanguage()
  const [plan, setPlan] = useState<TherapyPlan | null>(null)
  const [focus, setFocus] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    try {
      const { data } = await api.get('/api/patient/therapy-plan')
      setPlan(data.plan)
    } catch {
      setError(t.therapyPlan.loadError)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const generate = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const { data } = await api.post('/api/patient/therapy-plan/generate', { focus: focus || undefined })
      setPlan(data.plan)
      setSuccess('Your weekly plan is ready. Review your goals below.')
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error
      setError(msg || t.therapyPlan.generateError)
    } finally {
      setLoading(false)
    }
  }

  const downloadPdf = async () => {
    try {
      const res = await api.get('/api/patient/therapy-plan/pdf', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'therapy_plan.pdf'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      setError(t.therapyPlan.pdfError)
    }
  }

  const Section = ({
    icon: Icon,
    title,
    items,
  }: {
    icon: typeof Target
    title: string
    items: string[]
  }) => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Icon className="h-4 w-4 text-primary" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {items.map((item, i) => (
            <li key={i} className="flex gap-2 text-sm">
              <span className="text-primary font-medium">{i + 1}.</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl w-full flex-1 flex flex-col p-4 md:p-6 gap-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-calm-900 flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              {t.therapyPlan.title}
            </h1>
            <p className="text-muted-foreground mt-1">{t.therapyPlan.subtitle}</p>
          </div>
          {plan?.has_pdf && (
            <Button variant="outline" onClick={downloadPdf}>
              <Download className="h-4 w-4 mr-2" />
              {t.therapyPlan.downloadPdf}
            </Button>
          )}
        </div>

        <Card className="border-dashed border-primary/30 bg-gradient-to-br from-calm-50/80 to-primary/5 dark:from-calm-950/20 dark:to-primary/5">
          <CardHeader>
            <CardTitle className="text-base">{t.therapyPlan.generateTitle}</CardTitle>
            <CardDescription>{t.therapyPlan.generateDesc}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {FOCUS_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  disabled={loading}
                  onClick={() => setFocus(chip.toLowerCase())}
                  className={cn(
                    'text-xs px-3 py-1.5 rounded-full border transition-colors',
                    focus.toLowerCase() === chip.toLowerCase()
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background hover:bg-muted border-border text-muted-foreground'
                  )}
                >
                  {chip}
                </button>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <Input
                placeholder={t.therapyPlan.focusPlaceholder}
                value={focus}
                onChange={(e) => setFocus(e.target.value)}
                disabled={loading}
                onKeyDown={(e) => e.key === 'Enter' && !loading && generate()}
              />
              <Button onClick={generate} disabled={loading} className="shrink-0 min-w-[140px]">
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    {t.therapyPlan.generating}
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    {plan ? t.therapyPlan.regenerate : t.therapyPlan.generate}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && <Alert className="border-destructive/50 bg-destructive/10 text-destructive">{error}</Alert>}
        {success && (
          <Alert className="border-emerald-200 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100 dark:border-emerald-800">
            <CheckCircle2 className="h-4 w-4" />
            <span className="ml-2">{success}</span>
          </Alert>
        )}

        {loading && !plan && (
          <Card className="animate-pulse">
            <CardContent className="pt-6 space-y-3">
              <div className="h-4 bg-muted rounded w-3/4" />
              <div className="h-4 bg-muted rounded w-full" />
              <div className="h-4 bg-muted rounded w-5/6" />
              <p className="text-sm text-muted-foreground pt-2">Building your personalized plan…</p>
            </CardContent>
          </Card>
        )}

        {plan ? (
          <div className="space-y-4 animate-fade-up">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="secondary">{t.therapyPlan.aiGenerated}</Badge>
              {plan.created_at && (
                <span className="text-xs text-muted-foreground">
                  Created {new Date(plan.created_at).toLocaleDateString()}
                </span>
              )}
            </div>
            {plan.summary && (
              <Card className="bg-primary/5 border-primary/20">
                <CardContent className="pt-6 text-sm text-calm-900">{plan.summary}</CardContent>
              </Card>
            )}
            <Section icon={Target} title={t.therapyPlan.weeklyGoals} items={plan.weekly_goals} />
            <Section icon={ListChecks} title={t.therapyPlan.copingTasks} items={plan.coping_tasks} />
            <Section icon={Lightbulb} title={t.therapyPlan.behavioralSuggestions} items={plan.behavioral_suggestions} />
            <p className="text-xs text-muted-foreground text-center pb-4">{t.therapyPlan.disclaimer}</p>
          </div>
        ) : (
          !loading && (
            <div className="text-center py-12 text-muted-foreground">
              <Sparkles className="h-10 w-10 mx-auto mb-3 text-calm-300" />
              <p>{t.therapyPlan.emptyTitle}</p>
              <p className="text-sm mt-2">{t.therapyPlan.emptyHint}</p>
            </div>
          )
        )}
      </div>
    </AppLayout>
  )
}
