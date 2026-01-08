/**
 * App component - root component for the AI Digital Twin frontend.
 * Provides the main layout with chat window and notes section.
 */

import React from 'react'
import { ChatWindow, NotesSection } from './components'
import { useChat } from './hooks/useChat'

/**
 * Header component - displays title, description, and new chat button
 * @param {Object} props
 * @param {Function} props.onNewChat - Handler for starting new chat
 * @param {boolean} props.hasMessages - Whether there are messages to clear
 */
function Header({ onNewChat, hasMessages }) {
  return (
    <header className="header">
      <div className="header-content">
        <div>
          <h1>AI Digital Twin</h1>
          <p>Chat with my AI representation to learn more about me</p>
        </div>
        {hasMessages && (
          <button className="new-chat-btn" onClick={onNewChat}>
            New Chat
          </button>
        )}
      </div>
    </header>
  )
}

/**
 * Main App component
 */
function App() {
  const { messages, isLoading, error, sendMessage, clearConversation } = useChat()

  return (
    <div className="app">
      <Header onNewChat={clearConversation} hasMessages={messages.length > 0} />
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        error={error}
        onSendMessage={sendMessage}
      />
      <NotesSection />
    </div>
  )
}

export default App
