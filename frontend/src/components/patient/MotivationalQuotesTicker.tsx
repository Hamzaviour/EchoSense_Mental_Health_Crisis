import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useLanguage } from '@/context/LanguageContext'

export default function MotivationalQuotesTicker({ crisisMode }: { crisisMode?: boolean }) {
  const { t } = useLanguage()
  const tickerText = t.quotes.map((q) => `✦ ${q}`).join('     ')

  return (
    <div
      className={cn(
        'relative overflow-hidden shrink-0 border-b',
        crisisMode
          ? 'bg-slate-800/60 border-slate-700'
          : 'bg-gradient-to-r from-calm-50/90 via-secondary/30 to-calm-50/90 border-calm-100'
      )}
      aria-live="polite"
      aria-label={t.chat.tickerLabel}
    >
      <div className="flex items-center gap-2 py-2.5">
        <div className="pl-4 shrink-0 flex items-center gap-1.5">
          <Sparkles
            className={cn('h-3.5 w-3.5', crisisMode ? 'text-calm-300' : 'text-primary')}
            aria-hidden
          />
          <span
            className={cn(
              'text-[10px] font-medium uppercase tracking-wider hidden sm:inline',
              crisisMode ? 'text-slate-400' : 'text-calm-600'
            )}
          >
            {t.chat.dailyCalm}
          </span>
        </div>
        <div className="flex-1 overflow-hidden mask-fade-edges">
          <div
            className={cn(
              'flex whitespace-nowrap animate-ticker w-max',
              crisisMode ? 'text-slate-300' : 'text-calm-800'
            )}
          >
            <span className="text-sm px-4">{tickerText}</span>
            <span className="text-sm px-4" aria-hidden>
              {tickerText}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
