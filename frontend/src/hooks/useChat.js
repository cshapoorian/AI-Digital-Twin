/**
 * Custom hook for managing chat state and API communication.
 * Handles message sending, loading states, and conversation persistence.
 */

import { useState, useCallback, useEffect } from 'react'

// Generate a UUID for conversation tracking
const generateId = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// Get or create conversation ID from session storage
const getConversationId = () => {
  let id = sessionStorage.getItem('conversationId')
  if (!id) {
    id = generateId()
    sessionStorage.setItem('conversationId', id)
  }
  return id
}

// API base URL - uses proxy in dev, env var in production
const API_URL = import.meta.env.VITE_API_URL || ''

/**
 * useChat hook - manages chat functionality
 *
 * @returns {Object} Chat state and functions
 */
export function useChat() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [conversationId, setConversationId] = useState(getConversationId)

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/api/health`)
        if (!response.ok) {
          setError('Unable to connect to the server. Please try again later.')
        }
      } catch (err) {
        setError('Unable to connect to the server. Please try again later.')
      }
    }
    checkHealth()
  }, [])

  /**
   * Send a message and get AI response
   * @param {string} content - The message content
   */
  const sendMessage = useCallback(async (content) => {
    if (!content.trim() || isLoading) return

    // Clear any previous error
    setError(null)

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
   * Clear the conversation and start fresh
   */
  const clearConversation = useCallback(() => {
    setMessages([])
    setError(null)
    // Generate new conversation ID and update both state and storage
    const newId = generateId()
    sessionStorage.setItem('conversationId', newId)
    setConversationId(newId)
  }, [])

  /**
   * Submit feedback about a message
   * @param {string} userMessage - The user's message
   * @param {string} assistantResponse - The AI's response
   * @param {string} feedbackType - Type of feedback
   * @param {string} notes - Optional notes
   */
  const submitFeedback = useCallback(async (userMessage, assistantResponse, feedbackType, notes = '') => {
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
          notes: notes,
        }),
      })
    } catch (err) {
      console.error('Feedback submission error:', err)
    }
  }, [conversationId])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearConversation,
    submitFeedback,
  }
}

export default useChat
