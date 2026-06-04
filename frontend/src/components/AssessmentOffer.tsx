import { Button } from '@/components/ui/button'
import { useAssessment } from '@/context/AssessmentContext'
import { useLanguage } from '@/context/LanguageContext'

export default function AssessmentOffer({
  offer,
  onLater,
}: {
  offer: { offered?: boolean; session_id?: number }
  onLater?: () => void
}) {
  const { acceptOffer, declineOffer } = useAssessment()
  const { t } = useLanguage()
  if (!offer?.session_id) return null

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      <Button size="sm" onClick={() => acceptOffer(offer.session_id!)}>
        {t.assessment.yesContinue}
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          declineOffer(offer.session_id!)
          onLater?.()
        }}
      >
        {t.assessment.maybeLater}
      </Button>
    </div>
  )
}
