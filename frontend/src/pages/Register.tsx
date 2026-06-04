import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { Heart } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'

export default function Register() {
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', phone: '', age: '', gender: 'other',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register({ ...form, age: parseInt(form.age) })
      navigate('/chat')
    } catch {
      setError('Registration failed. Email may already be in use.')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-calm-50 via-background to-secondary/30">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-lg">
        <div className="text-center mb-6">
          <Heart className="h-8 w-8 text-primary mx-auto mb-2" />
          <h1 className="text-xl font-semibold text-calm-900">Join Echo Sense</h1>
          <p className="text-sm text-muted-foreground">A safe, judgment-free space for support</p>
        </div>
        <Card className="shadow-lg shadow-calm-900/5">
          <CardHeader>
            <CardTitle>Patient registration</CardTitle>
            <CardDescription>Your information is kept private and secure</CardDescription>
          </CardHeader>
          <CardContent>
            {error && <Alert className="mb-4">{error}</Alert>}
            <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label>Full name</Label>
                <Input value={form.full_name} onChange={set('full_name')} required />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Email</Label>
                <Input type="email" value={form.email} onChange={set('email')} required />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Password</Label>
                <Input type="password" value={form.password} onChange={set('password')} required />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input value={form.phone} onChange={set('phone')} required />
              </div>
              <div className="space-y-2">
                <Label>Age</Label>
                <Input type="number" value={form.age} onChange={set('age')} required />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Gender</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.gender}
                  onChange={set('gender')}
                >
                  {['male', 'female', 'other', 'prefer_not_to_say'].map((g) => (
                    <option key={g} value={g}>{g.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>
              <Button type="submit" className="sm:col-span-2 mt-2" disabled={loading}>
                {loading ? 'Creating account...' : 'Create account'}
              </Button>
            </form>
            <p className="text-center text-sm text-muted-foreground mt-4">
              Already registered? <Link to="/login" className="text-primary hover:underline">Sign in</Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
