import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { useLanguage } from '@/context/LanguageContext'

export default function ConsentModal({
  open,
  onAccept,
}: {
  open: boolean
  onAccept: (data: { consent: boolean; privacy_accepted: boolean }) => void
}) {
  const { t } = useLanguage()
  const [consent, setConsent] = useState(false)
  const [privacy, setPrivacy] = useState(false)

  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="text-calm-900">{t.consent.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 text-sm text-muted-foreground">
          <p>{t.consent.p1}</p>
          <p>{t.consent.p2}</p>
          <p className="text-calm-700 font-medium">{t.consent.crisis}</p>
          <label className="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
            <span>{t.consent.consentCheck}</span>
          </label>
          <label className="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" checked={privacy} onChange={(e) => setPrivacy(e.target.checked)} className="mt-1" />
            <span>{t.consent.privacyCheck}</span>
          </label>
          <Button
            className="w-full"
            disabled={!consent || !privacy}
            onClick={() => onAccept({ consent: true, privacy_accepted: true })}
          >
            {t.consent.continue}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
