/**
 * ChatWindow component - main chat interface.
 * Contains message list, typing indicator, and input form.
 */

import React, { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'

/**
 * TypingIndicator - shows when AI is generating a response
 */
function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
    </div>
  )
}

/**
 * WelcomeMessage - shown when chat is empty
 */
function WelcomeMessage() {
  return (
    <div className="welcome-message">
      <h2>Welcome!</h2>
      <p>
        I'm an AI representation of the person who created me.
        Feel free to ask me about my hobbies, work, interests, or anything else you'd like to know!
      </p>
    </div>
  )
}

/**
 * ChatWindow component
 * @param {Object} props
 * @param {Array} props.messages - Array of message objects
 * @param {boolean} props.isLoading - Whether AI is generating
 * @param {string} props.error - Error message if any
 * @param {Function} props.onSendMessage - Handler for sending messages
 */
function ChatWindow({ messages, isLoading, error, onSendMessage }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input)
      setInput('')
    }
  }

  // Handle Enter key (submit) vs Shift+Enter (newline)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}

        {isLoading && <TypingIndicator />}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

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
          <button
            type="submit"
            className="chat-submit"
            disabled={isLoading || !input.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatWindow
