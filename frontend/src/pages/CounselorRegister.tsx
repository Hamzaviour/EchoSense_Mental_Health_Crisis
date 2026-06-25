import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { Heart, Stethoscope } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import PhoneInput, { formatFullPhone } from '@/components/PhoneInput'
import { homeRouteForRole } from '@/config/navigation'

const SPECIALIZATIONS = [
  'General Counseling',
  'Crisis Intervention',
  'Anxiety & Depression',
  'Trauma & PTSD',
  'Youth Counseling',
  'Family Therapy',
  'Other',
]

export default function CounselorRegister() {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    specialization: SPECIALIZATIONS[0],
  })
  const [phoneDialCode, setPhoneDialCode] = useState('+92')
  const [phoneLocal, setPhoneLocal] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { registerCounselor } = useAuth()
  const navigate = useNavigate()

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const phoneDigits = phoneLocal.replace(/\D/g, '')
    if (phoneDigits.length > 0 && phoneDigits.length < 7) {
      setError('Please enter a valid phone number (at least 7 digits), or leave it blank.')
      return
    }
    const phone = phoneDigits.length >= 7 ? formatFullPhone(phoneDialCode, phoneLocal) : undefined
    setLoading(true)
    try {
      const data = await registerCounselor({ ...form, phone }) as { user: { role: string } }
      navigate(homeRouteForRole(data.user.role))
    } catch {
      setError('Registration failed. Email may already be in use.')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-calm-50 via-background to-secondary/30">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-lg">
        <div className="text-center mb-6">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 mb-2">
            <Stethoscope className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-xl font-semibold text-calm-900">Counselor registration</h1>
          <p className="text-sm text-muted-foreground">Join Echo Sense as a licensed support professional</p>
        </div>
        <Card className="shadow-lg shadow-calm-900/5">
          <CardHeader>
            <CardTitle>Create counselor account</CardTitle>
            <CardDescription>Access triage, patient navigator, and decision workspace tools</CardDescription>
          </CardHeader>
          <CardContent>
            {error && <Alert className="mb-4">{error}</Alert>}
            <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label>Full name</Label>
                <Input value={form.full_name} onChange={set('full_name')} required placeholder="Dr. Jane Smith" />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Email</Label>
                <Input type="email" value={form.email} onChange={set('email')} required placeholder="counselor@clinic.com" />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Password</Label>
                <Input type="password" value={form.password} onChange={set('password')} required minLength={6} />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="counselor-phone">Phone (optional)</Label>
                <PhoneInput
                  id="counselor-phone"
                  dialCode={phoneDialCode}
                  localNumber={phoneLocal}
                  onDialCodeChange={setPhoneDialCode}
                  onLocalNumberChange={setPhoneLocal}
                />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Specialization</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.specialization}
                  onChange={set('specialization')}
                >
                  {SPECIALIZATIONS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <Button type="submit" className="sm:col-span-2 mt-2" disabled={loading}>
                {loading ? 'Creating account...' : 'Register as counselor'}
              </Button>
            </form>
            <p className="text-center text-sm text-muted-foreground mt-4">
              Already registered?{' '}
              <Link to="/login" className="text-primary hover:underline">Sign in</Link>
            </p>
            <p className="text-center text-sm text-muted-foreground mt-2">
              Registering as a patient?{' '}
              <Link to="/register" className="text-primary hover:underline inline-flex items-center gap-1">
                <Heart className="h-3.5 w-3.5" /> Patient sign up
              </Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
