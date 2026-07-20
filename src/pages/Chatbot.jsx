import React, { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import '../components/Chatbot.css'
import PersibLogo from '../image/Logo_Persib_Bandung.png'
import { chatAPI, tokenManager } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { getTranslation } from '../utils/translation'

function Chatbot() {
  const { logout, user } = useAuth()
  const t = getTranslation(user?.referensi_bahasa)
  const [isNewChat, setIsNewChat] = useState(true)
  const [inputMessage, setInputMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const resetToWelcome = () => {
    setIsNewChat(true)
    setMessages([])
    setInputMessage('')
    setIsSidebarOpen(false)
  }

  const startChatSession = async () => {
    setIsNewChat(false)
    setIsLoading(true)
    setMessages([])
    setIsSidebarOpen(false)

    try {
      const response = await chatAPI.startChat()
      const botResponse = {
        id: Date.now(),
        text: response.response || 'Selamat datang di MaungBot Persib!',
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages([botResponse])
    } catch (error) {
      console.error('Failed to start chat:', error)
      const errorMessage = {
        id: Date.now(),
        text: `Gagal memulai percakapan: ${error.message}`,
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages([errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (e, messageText = null) => {
    if (e) e.preventDefault()
    
    const textToSend = messageText || inputMessage
    if (textToSend.trim() === '' || textToSend.length > 500) return

    if (isNewChat) {
      setIsNewChat(false)
    }

    // Tambah pesan user
    const newUserMessage = {
      id: Date.now(),
      text: textToSend,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, newUserMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      // Kirim ke API HFSM
      const response = await chatAPI.sendMessage(textToSend)
      
      // Tambah respons bot
      const botResponse = {
        id: Date.now() + 1,
        text: response.response || 'Maaf, saya tidak dapat memproses pertanyaan Anda.',
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prevMessages => [...prevMessages, botResponse])
    } catch (error) {
      console.error('Chat error:', error)
      
      // Tambah error message
      const errorMessage = {
        id: Date.now() + 1,
        text: `Maaf, terjadi kesalahan: ${error.message}`,
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prevMessages => [...prevMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user || !user.nama_lengkap) return 'U'
    const names = user.nama_lengkap.trim().split(' ')
    if (names.length >= 2) {
      return (names[0][0] + names[1][0]).toUpperCase()
    }
    return names[0][0].toUpperCase()
  }

  return (
    <div className="cb-main">
      {/* Sidebar Overlay for Mobile */}
      <div 
        className={`cb-sidebar-overlay ${isSidebarOpen ? 'visible' : ''}`} 
        onClick={() => setIsSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`cb-sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="cb-sidebar-header">
          <div className="cb-bot-icon">🤖</div>
          <div className="cb-bot-title">
            <h3>MAUNG BOT</h3>
            <p>Powered by HFSM</p>
          </div>
          {/* Close Button for Mobile Sidebar */}
          <button className="cb-close-sidebar-btn" onClick={() => setIsSidebarOpen(false)} aria-label="Tutup Menu">
            ✕
          </button>
        </div>

        <button className="cb-new-chat-btn" onClick={resetToWelcome}>
          <span>➕ Obrolan Baru</span>
        </button>

        <div className="cb-sidebar-menu">
          <h4>MENU UTAMA</h4>
          <button className="cb-menu-item active" style={{ width: '100%', textAlign: 'left', border: 'none', background: 'transparent', cursor: 'pointer' }} onClick={resetToWelcome}>
            💬 Chat Sekarang
          </button>
        </div>

        <div className="cb-sidebar-footer">
          <h4>USER</h4>
          <Link to="/profile" className="cb-menu-item" onClick={() => setIsSidebarOpen(false)}>
            👤 Edit Profil
          </Link>
          <h4>PENGATURAN</h4>
          <Link to="/settings" className="cb-settings-item" onClick={() => setIsSidebarOpen(false)}>
            <span>⚙️ Settings</span>
          </Link>
        </div>

        <button className="cb-logout-btn" onClick={handleLogout}>Keluar</button>
      </aside>

      {/* Main Chat Area */}
      <main className="cb-chatbot-container">
        {/* Top Header for Mobile */}
        <header className="cb-top-header">
          <button className="cb-menu-toggle-btn" onClick={() => setIsSidebarOpen(true)} aria-label="Buka Menu">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
          </button>
          <div className="cb-header-title">
            <h3>MAUNG BOT</h3>
          </div>
          <button className="cb-header-new-chat" onClick={resetToWelcome} title="Obrolan Baru">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
          </button>
        </header>

        {isNewChat ? (
          /* Empty / Welcome Chat State (Bersih tanpa quick questions) */
          <div className="cb-empty-chat-state">
            <div className="cb-logo-container">
              <img src={PersibLogo} alt="Persib Logo" className="cb-persib-logo" />
            </div>
            <h1 className="cb-welcome-title">
              {user?.referensi_bahasa === "eng" ? "Start a new chat with " : "Mulai obrolan baru dengan "}
              <span className="cb-highlight">Maung Chat</span>
            </h1>
            <p className="cb-welcome-subtitle">
              Layanan customer service resmi Persib Bandung berbasis HFSM.
            </p>

            <button 
              className="cb-new-chat-btn" 
              onClick={startChatSession}
              disabled={isLoading}
              style={{ marginTop: '16px', padding: '14px 28px', fontSize: '15px' }}
            >
              <span>💬 Mulai Percakapan MaungBot</span>
            </button>
          </div>
        ) : (
          /* Active Chat View */
          <div className="cb-chat-view">
            <div className="cb-messages-container">
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`cb-message ${message.sender === 'user' ? 'cb-user-message' : 'cb-bot-message'}`}
                >
                  {message.sender === 'bot' && (
                    <div className="cb-message-avatar cb-avatar-bot">
                      <img src={PersibLogo} alt="Maung Bot" />
                    </div>
                  )}
                  <div className="cb-message-bubble">
                    <p>{message.text}</p>
                    <span className="cb-message-time">{formatTime(message.timestamp)}</span>
                  </div>
                  {message.sender === 'user' && (
                    <div className="cb-message-avatar cb-avatar-user">
                      {getUserInitials()}
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="cb-message cb-bot-message">
                  <div className="cb-message-avatar cb-avatar-bot">
                    <img src={PersibLogo} alt="Maung Bot" />
                  </div>
                  <div className="cb-message-bubble cb-typing-bubble">
                    <div className="cb-typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* Input Form */}
        <form className="cb-chat-input-form" onSubmit={handleSendMessage}>
          <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column' }}>
            <input
              type="text"
              className="cb-chat-input"
              placeholder={t.chatbot_placeholder}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={isLoading}
            />
            {inputMessage.length > 400 && (
              <span style={{ 
                position: 'absolute', 
                right: '12px', 
                bottom: '-20px', 
                fontSize: '11px', 
                color: inputMessage.length > 500 ? '#ef4444' : '#e2e8f0',
                transition: 'color 0.2s'
              }}>
                {inputMessage.length}/500
              </span>
            )}
          </div>
          <button 
            type="submit" 
            className="cb-send-button" 
            disabled={isLoading || inputMessage.trim().length === 0 || inputMessage.length > 500}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </form>
      </main>
    </div>
  )
}

export default Chatbot
