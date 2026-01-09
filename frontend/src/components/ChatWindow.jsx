/**
 * ChatWindow component - main chat interface.
 * Contains message list, typing indicator, input form, and feedback modal.
 */

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import MessageBubble from './MessageBubble'
import FeedbackModal from './FeedbackModal'

/**
 * TypingIndicator - shows when AI is generating a response
 */
function TypingIndicator() {
  return (
    <motion.div
      className="typing-indicator"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
    </motion.div>
  )
}

/**
 * WelcomeMessage - shown when chat is empty
 */
function WelcomeMessage() {
  return (
    <motion.div
      className="welcome-message"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="welcome-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </div>
      <h2>Hello there</h2>
      <p>
        Welcome to Cameron Shapoorian's AI Digital Twin. This conversational interface
        provides insights into Cameron's professional background, skills, and experience.
      </p>
      <p className="welcome-subtext">
        Feel free to ask about his work experience, technical skills, what he's looking for, or why he'd be a good fit for your team.
      </p>
      <p className="server-notice">
        First message may take a moment if the server is waking up.
      </p>
    </motion.div>
  )
}

/**
 * ChatWindow component
 * @param {Object} props
 * @param {Array} props.messages - Array of message objects
 * @param {boolean} props.isLoading - Whether AI is generating
 * @param {string} props.error - Error message if any
 * @param {Function} props.onSendMessage - Handler for sending messages
 * @param {Function} props.onRetry - Handler for retrying failed messages
 * @param {Function} props.onSubmitFeedback - Handler for submitting feedback
 * @param {Object} props.feedbackState - Current feedback state by message ID
 * @param {Function} props.getUserMessageBefore - Get user message before an assistant message
 */
function ChatWindow({
  messages,
  isLoading,
  error,
  onSendMessage,
  onRetry,
  onSubmitFeedback,
  feedbackState,
  getUserMessageBefore,
}) {
  const [input, setInput] = useState('')
  const [feedbackModal, setFeedbackModal] = useState({
    isOpen: false,
    rating: null,
    messageId: null,
    messageIndex: null,
    assistantResponse: null,
  })
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Focus input on mount and after loading completes
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Refocus input when AI finishes responding
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [isLoading])

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input)
      setInput('')
      // Refocus input after sending (use setTimeout for mobile compatibility)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  // Handle Enter key (submit) vs Shift+Enter (newline)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Handle feedback button click
  const handleFeedbackClick = (messageId, messageIndex, assistantResponse, rating) => {
    setFeedbackModal({
      isOpen: true,
      rating,
      messageId,
      messageIndex,
      assistantResponse,
    })
  }

  // Handle feedback submission
  const handleFeedbackSubmit = (feedbackType, notes) => {
    const { messageId, messageIndex, assistantResponse, rating } = feedbackModal
    const userMessage = getUserMessageBefore(messageIndex)

    onSubmitFeedback(messageId, userMessage, assistantResponse, rating, feedbackType, notes)
    setFeedbackModal({ isOpen: false, rating: null, messageId: null, messageIndex: null, assistantResponse: null })
  }

  // Close feedback modal
  const handleFeedbackClose = () => {
    setFeedbackModal({ isOpen: false, rating: null, messageId: null, messageIndex: null, assistantResponse: null })
  }

  return (
    <>
      <motion.div
        className="chat-container"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <div className="chat-messages">
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <WelcomeMessage key="welcome" />
            ) : (
              messages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  feedbackGiven={feedbackState[message.id] || null}
                  onFeedback={(rating) => handleFeedbackClick(message.id, index, message.content, rating)}
                  onRetry={message.isError ? onRetry : null}
                />
              ))
            )}
          </AnimatePresence>

          <AnimatePresence>
            {isLoading && <TypingIndicator key="typing" />}
          </AnimatePresence>

          <AnimatePresence>
            {error && (
              <motion.div
                className="error-message"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <form className="chat-input-form" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              disabled={isLoading}
              maxLength={2000}
            />
            <motion.button
              type="submit"
              className="chat-submit"
              disabled={isLoading || !input.trim()}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </motion.button>
          </form>
        </div>
      </motion.div>

      <FeedbackModal
        isOpen={feedbackModal.isOpen}
        rating={feedbackModal.rating}
        onSubmit={handleFeedbackSubmit}
        onClose={handleFeedbackClose}
      />
    </>
  )
}

export default ChatWindow
