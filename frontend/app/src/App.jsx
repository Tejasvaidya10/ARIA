import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import EvalPage from './pages/EvalPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/app" element={<DashboardPage />} />
      <Route path="/eval" element={<EvalPage />} />
    </Routes>
  )
}
