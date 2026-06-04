export type CaseSummary = {
  patient_id: string
  full_name: string
  conversation_summary: string
  ai_clinical_summary: string
  risk_score: number | null
  risk_level: string | null
  sentiment_average: number | null
  sentiment_distribution: Record<string, number>
  sentiment_trend: string
  trigger_keywords: string[]
  assessments: {
    phq9?: { score: number; severity: string } | null
    gad7?: { score: number; severity: string } | null
  }
  escalation_status: string | null
  counselor_notes: string
  generated_at: string
}
