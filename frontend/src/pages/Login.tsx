import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Heart, Sparkles } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import LanguageToggle from '@/components/LanguageToggle'
import ThemeToggle from '@/components/ThemeToggle'
import { homeRouteForRole } from '@/config/navigation'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password) as { user: { role: string } }
      navigate(homeRouteForRole(data.user.role))
    } catch {
      setError('Invalid email or password')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-calm-50 via-background to-secondary/30 relative">
      <div className="absolute top-4 right-4 flex gap-2">
        <LanguageToggle />
        <ThemeToggle />
      </div>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 mb-4"
          >
            <Heart className="h-7 w-7 text-primary" />
          </motion.div>
          <h1 className="text-2xl font-semibold text-calm-900">Echo Sense</h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center justify-center gap-1">
            <Sparkles className="h-3.5 w-3.5" /> Calm Clinical AI Copilot
          </p>
        </div>
        <Card className="border-border/60 shadow-lg shadow-calm-900/5">
          <CardHeader>
            <CardTitle>Welcome back</CardTitle>
            <CardDescription>Sign in to continue your safe space</CardDescription>
          </CardHeader>
          <CardContent>
            {error && <Alert variant="calm" className="mb-4 border-destructive/30 bg-destructive/5 text-destructive">{error}</Alert>}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>
            <p className="text-center text-sm text-muted-foreground mt-6">
              New patient?{' '}
              <Link to="/register" className="text-primary font-medium hover:underline">Create account</Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
