/**
 * NotesSection component - displays static notes from the owner.
 * This is a placeholder for the owner to add content about AI digital twins
 * and the implications of using them at scale.
 */

import React from 'react'

/**
 * NotesSection component
 * TODO: Owner should customize this content with their thoughts on
 * AI digital twins and human interaction.
 */
function NotesSection() {
  return (
    <div className="notes-container">
      <h2>A Note From Me</h2>
      <div className="notes-content">
        <div className="notes-placeholder">
          <p>
            <strong>Content coming soon...</strong>
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            This space is reserved for my thoughts on AI digital twins
            and why I think it's important to consider their implications
            for human connection and interaction.
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            In the meantime, feel free to chat with my AI twin to learn
            more about me!
          </p>
        </div>
      </div>
    </div>
  )
}

export default NotesSection
