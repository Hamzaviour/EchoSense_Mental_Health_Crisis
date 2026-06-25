import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

export type CountryCodeOption = {
  dial: string
  label: string
}

/** Common dial codes — Pakistan first (default for Echo Sense). */
export const COUNTRY_CODES: CountryCodeOption[] = [
  { dial: '+92', label: 'PK +92' },
  { dial: '+1', label: 'US +1' },
  { dial: '+44', label: 'UK +44' },
  { dial: '+971', label: 'AE +971' },
  { dial: '+966', label: 'SA +966' },
  { dial: '+91', label: 'IN +91' },
  { dial: '+86', label: 'CN +86' },
  { dial: '+61', label: 'AU +61' },
  { dial: '+49', label: 'DE +49' },
  { dial: '+33', label: 'FR +33' },
  { dial: '+39', label: 'IT +39' },
  { dial: '+34', label: 'ES +34' },
  { dial: '+81', label: 'JP +81' },
  { dial: '+82', label: 'KR +82' },
  { dial: '+60', label: 'MY +60' },
  { dial: '+65', label: 'SG +65' },
  { dial: '+880', label: 'BD +880' },
  { dial: '+94', label: 'LK +94' },
  { dial: '+93', label: 'AF +93' },
  { dial: '+974', label: 'QA +974' },
  { dial: '+968', label: 'OM +968' },
  { dial: '+973', label: 'BH +973' },
  { dial: '+965', label: 'KW +965' },
  { dial: '+27', label: 'ZA +27' },
  { dial: '+234', label: 'NG +234' },
  { dial: '+20', label: 'EG +20' },
  { dial: '+90', label: 'TR +90' },
  { dial: '+7', label: 'RU +7' },
  { dial: '+55', label: 'BR +55' },
  { dial: '+52', label: 'MX +52' },
]

export function formatFullPhone(dialCode: string, localNumber: string): string {
  const digits = localNumber.replace(/\D/g, '')
  if (!digits) return ''
  return `${dialCode}${digits}`
}

export function parseStoredPhone(full: string): { dialCode: string; localNumber: string } {
  const trimmed = (full || '').trim()
  if (!trimmed) return { dialCode: '+92', localNumber: '' }
  const match = COUNTRY_CODES.map((c) => c.dial)
    .sort((a, b) => b.length - a.length)
    .find((d) => trimmed.startsWith(d))
  if (match) {
    return { dialCode: match, localNumber: trimmed.slice(match.length).replace(/\D/g, '') }
  }
  if (trimmed.startsWith('+')) {
    const m = trimmed.match(/^(\+\d{1,4})(.*)$/)
    if (m) return { dialCode: m[1], localNumber: m[2].replace(/\D/g, '') }
  }
  return { dialCode: '+92', localNumber: trimmed.replace(/\D/g, '') }
}

type PhoneInputProps = {
  dialCode: string
  localNumber: string
  onDialCodeChange: (code: string) => void
  onLocalNumberChange: (number: string) => void
  required?: boolean
  disabled?: boolean
  className?: string
  id?: string
}

export default function PhoneInput({
  dialCode,
  localNumber,
  onDialCodeChange,
  onLocalNumberChange,
  required,
  disabled,
  className,
  id,
}: PhoneInputProps) {
  return (
    <div className={cn('flex gap-2', className)}>
      <select
        id={id ? `${id}-country` : undefined}
        aria-label="Country code"
        value={dialCode}
        onChange={(e) => onDialCodeChange(e.target.value)}
        disabled={disabled}
        required={required}
        className="h-10 shrink-0 rounded-md border border-input bg-background px-2 text-sm min-w-[7.5rem] max-w-[9rem]"
      >
        {COUNTRY_CODES.map((c) => (
          <option key={c.dial} value={c.dial}>
            {c.label}
          </option>
        ))}
      </select>
      <Input
        id={id}
        type="tel"
        inputMode="tel"
        autoComplete="tel-national"
        placeholder="300 1234567"
        value={localNumber}
        onChange={(e) => onLocalNumberChange(e.target.value)}
        required={required}
        disabled={disabled}
        className="flex-1 min-w-0"
      />
    </div>
  )
}
