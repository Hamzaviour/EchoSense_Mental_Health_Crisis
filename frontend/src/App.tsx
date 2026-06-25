import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { homeRouteForRole } from '@/config/navigation'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import CounselorRegister from '@/pages/CounselorRegister'
import PatientChat from '@/pages/PatientChat'
import TherapyPlan from '@/pages/TherapyPlan'
import CopingTools from '@/pages/CopingTools'
import Journal from '@/pages/Journal'
import SessionRequestPage from '@/pages/SessionRequest'
import CounselorDashboard from '@/pages/CounselorDashboard'
import PatientNavigatorView from '@/pages/PatientNavigatorView'
import DecisionWorkspaceView from '@/pages/DecisionWorkspaceView'
import ChatSupportView from '@/pages/ChatSupportView'
import AdminAnalytics from '@/pages/AdminAnalytics'

function PrivateRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center text-muted-foreground">Loading...</div>
  if (!user) return <Navigate to="/login" />
  if (roles && !roles.includes(user.role)) return <Navigate to={homeRouteForRole(user.role)} replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/register/counselor" element={<CounselorRegister />} />
      <Route path="/chat" element={<PrivateRoute roles={['PATIENT']}><PatientChat /></PrivateRoute>} />
      <Route path="/journal" element={<PrivateRoute roles={['PATIENT']}><Journal /></PrivateRoute>} />
      <Route path="/session-request" element={<PrivateRoute roles={['PATIENT']}><SessionRequestPage /></PrivateRoute>} />
      <Route path="/therapy-plan" element={<PrivateRoute roles={['PATIENT']}><TherapyPlan /></PrivateRoute>} />
      <Route path="/coping-tools" element={<PrivateRoute roles={['PATIENT']}><CopingTools /></PrivateRoute>} />
      <Route path="/counselor/triage" element={<PrivateRoute roles={['COUNSELOR', 'ADMIN']}><CounselorDashboard /></PrivateRoute>} />
      <Route path="/counselor/navigator" element={<PrivateRoute roles={['COUNSELOR', 'ADMIN']}><PatientNavigatorView /></PrivateRoute>} />
      <Route path="/counselor/decision" element={<PrivateRoute roles={['COUNSELOR', 'ADMIN']}><DecisionWorkspaceView /></PrivateRoute>} />
      <Route path="/counselor/chat-support" element={<PrivateRoute roles={['COUNSELOR', 'ADMIN']}><ChatSupportView /></PrivateRoute>} />
      <Route path="/counselor" element={<Navigate to="/counselor/triage" replace />} />
      <Route path="/admin" element={<PrivateRoute roles={['ADMIN', 'COUNSELOR']}><AdminAnalytics /></PrivateRoute>} />
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  )
}
