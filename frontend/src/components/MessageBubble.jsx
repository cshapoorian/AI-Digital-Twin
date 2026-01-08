/**
 * MessageBubble component - displays a single chat message.
 * Styled differently for user vs assistant messages.
 */

import React from 'react'

/**
 * Format timestamp for display
 * @param {string} isoString - ISO timestamp
 * @returns {string} Formatted time string
 */
const formatTime = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/**
 * MessageBubble component
 * @param {Object} props
 * @param {Object} props.message - Message object with role, content, timestamp
 */
function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`message message--${message.role}`}>
      <div className="message-bubble">
        {message.content}
      </div>
      <span className="message-time">
        {formatTime(message.timestamp)}
      </span>
    </div>
  )
}

export default MessageBubble
