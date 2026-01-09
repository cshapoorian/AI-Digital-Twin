/**
 * Custom hook for managing chat state and API communication.
 * Handles message sending, loading states, conversation persistence,
 * feedback, retry, and analytics tracking.
 */

import { useState, useCallback, useEffect, useRef } from 'react'

// Generate a UUID for conversation tracking
const generateId = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// Storage keys
const STORAGE_KEYS = {
  conversationId: 'adt_conversationId',
  messages: 'adt_messages',
  feedbackState: 'adt_feedbackState',
}

// Get or create conversation ID from localStorage
const getConversationId = () => {
  let id = localStorage.getItem(STORAGE_KEYS.conversationId)
  if (!id) {
    id = generateId()
    localStorage.setItem(STORAGE_KEYS.conversationId, id)
  }
  return id
}

// Load messages from localStorage
const loadMessages = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.messages)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// Load feedback state from localStorage
const loadFeedbackState = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.feedbackState)
    return stored ? JSON.parse(stored) : {}
  } catch {
    return {}
  }
}

// API base URL - uses proxy in dev, env var in production
const API_URL = import.meta.env.VITE_API_URL || ''

/**
 * Track an analytics event
 */
const trackEvent = async (eventType, sessionId, metadata = null) => {
  try {
    await fetch(`${API_URL}/api/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        session_id: sessionId,
        metadata,
      }),
    })
  } catch (err) {
    // Silent fail for analytics
    console.debug('Analytics tracking failed:', err)
  }
}

/**
 * useChat hook - manages chat functionality
 *
 * @returns {Object} Chat state and functions
 */
export function useChat() {
  const [messages, setMessages] = useState(loadMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [conversationId, setConversationId] = useState(getConversationId)
  const [feedbackState, setFeedbackState] = useState(loadFeedbackState)
  const lastUserMessageRef = useRef(null)
  const hasTrackedVisit = useRef(false)

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify(messages))
  }, [messages])

  // Persist feedback state to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.feedbackState, JSON.stringify(feedbackState))
  }, [feedbackState])

  // Track visit on mount and check backend health
  useEffect(() => {
    const init = async () => {
      // Track visit (only once per session)
      if (!hasTrackedVisit.current) {
        hasTrackedVisit.current = true
        trackEvent('visit', conversationId)
      }

      // Health check
      try {
        const response = await fetch(`${API_URL}/api/health`)
        if (!response.ok) {
          setError('Unable to connect to the server. Please try again later.')
        }
      } catch (err) {
        setError('Unable to connect to the server. Please try again later.')
      }
    }
    init()
  }, [conversationId])

  /**
   * Send a message and get AI response
   * @param {string} content - The message content
   */
  const sendMessage = useCallback(async (content) => {
    if (!content.trim() || isLoading) return

    // Clear any previous error
    setError(null)

    // Store for potential retry
    lastUserMessageRef.current = content.trim()

    // Add user message to state immediately
    const userMessage = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      // Build history from current messages (excluding the one we just added)
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content.trim(),
          conversation_id: conversationId,
          history: history,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()

      // Track message event
      trackEvent('message', conversationId)

      // Add assistant response to state
      const assistantMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: data.metadata,
      }
      setMessages((prev) => [...prev, assistantMessage])

    } catch (err) {
      console.error('Chat error:', err)
      setError('Failed to get a response. Please try again.')

      // Add error message as assistant response
      const errorMessage = {
        id: generateId(),
        role: 'assistant',
        content: "I'm having trouble responding right now. Please try again in a moment.",
        timestamp: new Date().toISOString(),
        isError: true,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [messages, isLoading, conversationId])

  /**
   * Retry the last failed message
   */
  const retryLastMessage = useCallback(() => {
    if (!lastUserMessageRef.current) return

    // Remove the last two messages (user message and error response)
    setMessages((prev) => {
      const newMessages = [...prev]
      // Remove error message
      if (newMessages.length > 0 && newMessages[newMessages.length - 1].isError) {
        newMessages.pop()
      }
      // Remove user message
      if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'user') {
        newMessages.pop()
      }
      return newMessages
    })

    // Resend
    sendMessage(lastUserMessageRef.current)
  }, [sendMessage])

  /**
   * Clear the conversation and start fresh
   */
  const clearConversation = useCallback(() => {
    setMessages([])
    setFeedbackState({})
    setError(null)
    // Generate new conversation ID and update both state and storage
    const newId = generateId()
    localStorage.setItem(STORAGE_KEYS.conversationId, newId)
    localStorage.removeItem(STORAGE_KEYS.messages)
    localStorage.removeItem(STORAGE_KEYS.feedbackState)
    setConversationId(newId)
    lastUserMessageRef.current = null
  }, [])

  /**
   * Submit feedback about a message
   * @param {string} messageId - The message ID
   * @param {string} userMessage - The user's message that preceded this response
   * @param {string} assistantResponse - The AI's response
   * @param {string} rating - 'positive' or 'negative'
   * @param {string} feedbackType - Type of feedback
   * @param {string} notes - Optional notes
   */
  const submitFeedback = useCallback(async (messageId, userMessage, assistantResponse, rating, feedbackType, notes = '') => {
    // Update local feedback state
    setFeedbackState((prev) => ({
      ...prev,
      [messageId]: rating,
    }))

    try {
      await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          user_message: userMessage,
          assistant_response: assistantResponse,
          feedback_type: feedbackType,
          rating: rating,
          notes: notes,
        }),
      })
    } catch (err) {
      console.error('Feedback submission error:', err)
    }
  }, [conversationId])

  /**
   * Get the user message that preceded a given assistant message
   */
  const getUserMessageBefore = useCallback((messageIndex) => {
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        return messages[i].content
      }
    }
    return ''
  }, [messages])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearConversation,
    submitFeedback,
    retryLastMessage,
    feedbackState,
    getUserMessageBefore,
  }
}

export default useChat
