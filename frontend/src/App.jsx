/**
 * App component - root component for the AI Doppelganger frontend.
 * Provides the main layout with a modern, centered chat interface.
 */

import React from 'react'
import { motion } from 'framer-motion'
import { ChatWindow } from './components'
import { useChat } from './hooks/useChat'

/**
 * Header component - displays title, description, and new chat button
 * @param {Object} props
 * @param {Function} props.onNewChat - Handler for starting new chat
 * @param {boolean} props.hasMessages - Whether there are messages to clear
 */
function Header({ onNewChat, hasMessages }) {
  return (
    <motion.header
      className="header"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="header-content">
        <div className="header-text">
          <h1>Cameron's Digital Twin</h1>
        </div>
        {hasMessages && (
          <motion.button
            className="new-chat-btn"
            onClick={onNewChat}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            New Chat
          </motion.button>
        )}
      </div>
    </motion.header>
  )
}

/**
 * Main App component
 */
function App() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearConversation,
    submitFeedback,
    retryLastMessage,
    feedbackState,
    getUserMessageBefore,
  } = useChat()

  return (
    <div className="app">
      <div className="background-gradient" />
      <div className="app-container">
        <Header onNewChat={clearConversation} hasMessages={messages.length > 0} />
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onSendMessage={sendMessage}
          onRetry={retryLastMessage}
          onSubmitFeedback={submitFeedback}
          feedbackState={feedbackState}
          getUserMessageBefore={getUserMessageBefore}
        />
      </div>
    </div>
  )
}

export default App
