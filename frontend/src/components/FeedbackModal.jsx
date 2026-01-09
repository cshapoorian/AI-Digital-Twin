/**
 * FeedbackModal component - popup for collecting detailed feedback.
 * Shows when user clicks thumbs up or down on a message.
 */

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const FEEDBACK_OPTIONS = {
  positive: [
    { value: 'helpful', label: 'Helpful answer' },
    { value: 'accurate', label: 'Accurate information' },
    { value: 'good_tone', label: 'Good tone/personality' },
    { value: 'other', label: 'Other' },
  ],
  negative: [
    { value: 'unhelpful', label: "Didn't answer my question" },
    { value: 'inaccurate', label: 'Inaccurate information' },
    { value: 'inappropriate', label: 'Inappropriate response' },
    { value: 'other', label: 'Other' },
  ],
}

/**
 * FeedbackModal component
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {string} props.rating - 'positive' or 'negative'
 * @param {Function} props.onSubmit - Callback with (feedbackType, notes)
 * @param {Function} props.onClose - Callback to close modal
 */
function FeedbackModal({ isOpen, rating, onSubmit, onClose }) {
  const [selectedType, setSelectedType] = useState('')
  const [notes, setNotes] = useState('')

  const options = FEEDBACK_OPTIONS[rating] || []

  const handleSubmit = (e) => {
    e.preventDefault()
    if (selectedType) {
      onSubmit(selectedType, notes)
      setSelectedType('')
      setNotes('')
    }
  }

  const handleClose = () => {
    setSelectedType('')
    setNotes('')
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="feedback-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            className="feedback-modal"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.2 }}
          >
            <h3>{rating === 'positive' ? 'What did you like?' : 'What went wrong?'}</h3>

            <form onSubmit={handleSubmit}>
              <div className="feedback-options">
                {options.map((option) => (
                  <label key={option.value} className="feedback-option">
                    <input
                      type="radio"
                      name="feedbackType"
                      value={option.value}
                      checked={selectedType === option.value}
                      onChange={(e) => setSelectedType(e.target.value)}
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>

              <textarea
                className="feedback-notes"
                placeholder="Additional details (optional)"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                maxLength={500}
                rows={3}
              />

              <div className="feedback-actions">
                <button
                  type="button"
                  className="feedback-btn feedback-btn--cancel"
                  onClick={handleClose}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="feedback-btn feedback-btn--submit"
                  disabled={!selectedType}
                >
                  Submit
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default FeedbackModal
