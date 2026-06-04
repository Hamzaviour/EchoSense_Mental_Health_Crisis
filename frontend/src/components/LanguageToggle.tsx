import { Languages } from 'lucide-react'
import { useLanguage } from '@/context/LanguageContext'
import { cn } from '@/lib/utils'

export default function LanguageToggle({ className }: { className?: string }) {
  const { language, setLanguage, t } = useLanguage()

  return (
    <div
      className={cn('flex items-center gap-1 rounded-lg border bg-muted/50 p-0.5', className)}
      role="group"
      aria-label={t.lang.label}
    >
      <button
        type="button"
        onClick={() => setLanguage('en')}
        className={cn(
          'rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
          language === 'en'
            ? 'bg-background text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground'
        )}
      >
        {t.lang.english}
      </button>
      <button
        type="button"
        onClick={() => setLanguage('ur')}
        className={cn(
          'rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
          language === 'ur'
            ? 'bg-background text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground'
        )}
      >
        {t.lang.romanUrdu}
      </button>
      <Languages className="h-3.5 w-3.5 text-muted-foreground ml-0.5 hidden sm:block" aria-hidden />
    </div>
  )
}
