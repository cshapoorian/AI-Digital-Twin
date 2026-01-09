/**
 * MessageBubble component - displays a single chat message.
 * Styled differently for user vs assistant messages.
 * Includes feedback buttons (thumbs up/down) for assistant messages.
 */

import React, { useState } from 'react'
import { motion } from 'framer-motion'

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
 * ThumbsUp icon
 */
const ThumbsUpIcon = ({ filled }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
  </svg>
)

/**
 * ThumbsDown icon
 */
const ThumbsDownIcon = ({ filled }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
  </svg>
)

/**
 * Retry icon
 */
const RetryIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points="23 4 23 10 17 10" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
  </svg>
)

/**
 * MessageBubble component
 * @param {Object} props
 * @param {Object} props.message - Message object with role, content, timestamp
 * @param {Function} props.onFeedback - Callback for feedback (rating: 'positive' | 'negative')
 * @param {Function} props.onRetry - Callback to retry failed message
 * @param {string} props.feedbackGiven - Current feedback state ('positive', 'negative', or null)
 */
function MessageBubble({ message, onFeedback, onRetry, feedbackGiven }) {
  const isAssistant = message.role === 'assistant'
  const isError = message.isError

  return (
    <motion.div
      className={`message message--${message.role}`}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      layout
    >
      <div className="message-bubble">
        {message.content}
      </div>

      <div className="message-footer">
        <span className="message-time">
          {formatTime(message.timestamp)}
        </span>

        {/* Retry button for error messages */}
        {isError && onRetry && (
          <button
            className="message-action-btn retry-btn"
            onClick={onRetry}
            title="Try again"
          >
            <RetryIcon /> Retry
          </button>
        )}

        {/* Feedback buttons for assistant messages (not errors) */}
        {isAssistant && !isError && onFeedback && (
          <div className="message-feedback">
            <button
              className={`message-action-btn ${feedbackGiven === 'positive' ? 'active' : ''}`}
              onClick={() => onFeedback('positive')}
              title="Helpful"
              disabled={feedbackGiven !== null}
            >
              <ThumbsUpIcon filled={feedbackGiven === 'positive'} />
            </button>
            <button
              className={`message-action-btn ${feedbackGiven === 'negative' ? 'active' : ''}`}
              onClick={() => onFeedback('negative')}
              title="Not helpful"
              disabled={feedbackGiven !== null}
            >
              <ThumbsDownIcon filled={feedbackGiven === 'negative'} />
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default MessageBubble
