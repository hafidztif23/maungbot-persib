import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { tokenManager } from './services/api'

// Halaman (Pages)
import LandingPage from './pages/LandingPage'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import Chatbot from './pages/Chatbot'
import FsmAdmin from './pages/FsmAdmin'
import SignUp from './pages/SignUp'
import Login from './pages/Login'

import './App.css'

function App() {
  const isLoggedIn = tokenManager.isLoggedIn()
  const currentUser = tokenManager.getUser()
  const isAdmin = currentUser?.role === 'admin' || currentUser?.email?.includes('admin')

  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rute Utama */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/profile" element={isLoggedIn ? <Profile /> : <Navigate to="/login" replace />} />
          <Route path="/settings" element={isLoggedIn ? <Settings /> : <Navigate to="/login" replace />} />

          {/* Rute Auth (Login/Signup) */}
          <Route 
            path="/login" 
            element={!isLoggedIn ? <Login /> : <Navigate to="/chat" replace />} 
          />
          <Route 
            path="/signup" 
            element={!isLoggedIn ? <SignUp /> : <Navigate to="/chat" replace />} 
          />

          {/* Rute Chatbot */}
          <Route 
            path="/chat" 
            element={isLoggedIn ? <Chatbot /> : <Navigate to="/login" replace />} 
          />

          <Route
            path="/fsm-admin"
            element={isLoggedIn && isAdmin ? <FsmAdmin /> : <Navigate to="/chat" replace />}
          />

          {/* Fallback Rute */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App