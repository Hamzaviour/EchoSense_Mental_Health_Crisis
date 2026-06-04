import { useState } from 'react'
import { Download, FileText, Loader2, Save } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import api from '@/api/client'

type Props = {
  patientId: number
  patientCode: string
  counselorNotes: string
  onNotesChange: (notes: string) => void
}

export default function ClinicalReportPanel({
  patientId,
  patientCode,
  counselorNotes,
  onNotesChange,
}: Props) {
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [message, setMessage] = useState('')

  const saveNotes = async () => {
    setSaving(true)
    setMessage('')
    try {
      await api.patch(`/api/counselor/patients/${patientId}/clinical-notes`, {
        counselor_notes: counselorNotes,
      })
      setMessage('Counselor notes saved.')
    } catch {
      setMessage('Failed to save notes.')
    } finally {
      setSaving(false)
    }
  }

  const downloadReport = async () => {
    setDownloading(true)
    setMessage('')
    try {
      const res = await api.post(
        `/api/counselor/patients/${patientId}/clinical-report/pdf`,
        { counselor_notes: counselorNotes },
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `clinical_case_${patientCode}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
      setMessage('Clinical case report downloaded.')
    } catch {
      setMessage('Failed to generate PDF report.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Generate Clinical Case Report
        </CardTitle>
        <p className="text-[10px] text-muted-foreground font-normal">
          Structured PDF with identity, AI summaries, sentiment, risk, assessments, and escalation status
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <label className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Counselor Notes (Section 7)
          </label>
          <textarea
            className="mt-1 flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Add manual clinical notes for this patient…"
            value={counselorNotes}
            onChange={(e) => onNotesChange(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={saveNotes} disabled={saving}>
            {saving ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}
            Save Notes
          </Button>
          <Button size="sm" onClick={downloadReport} disabled={downloading}>
            {downloading ? (
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            ) : (
              <Download className="h-3 w-3 mr-1" />
            )}
            Download Patient Report (PDF)
          </Button>
        </div>
        {message && <Alert className="py-2 text-xs">{message}</Alert>}
      </CardContent>
    </Card>
  )
}
