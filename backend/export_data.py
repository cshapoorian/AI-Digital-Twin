#!/usr/bin/env python3
"""
Export conversations and feedback from the database to a markdown file.

Usage:
    python export_data.py

Output:
    Creates/updates CONVERSATIONS_EXPORT.md in the repo root
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Paths
DB_PATH = Path(__file__).parent / "db" / "adt.db"
OUTPUT_PATH = Path(__file__).parent.parent / "CONVERSATIONS_EXPORT.md"


def get_connection():
    """Get database connection."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


def export_feedback(conn) -> str:
    """Export all feedback entries."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, conversation_id, user_message, assistant_response,
               feedback_type, notes, created_at
        FROM feedback
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        return "## Feedback\n\nNo feedback recorded yet.\n"

    lines = ["## Feedback\n"]
    lines.append(f"*{len(rows)} entries*\n")

    for row in rows:
        id_, conv_id, user_msg, assistant_resp, fb_type, notes, created_at = row
        lines.append(f"### Feedback #{id_} ({fb_type})")
        lines.append(f"**Date:** {created_at}")
        if conv_id:
            lines.append(f"**Conversation:** `{conv_id[:8]}...`")
        lines.append(f"\n**User asked:** {user_msg}")
        if assistant_resp:
            lines.append(f"\n**Assistant said:** {assistant_resp[:500]}{'...' if len(assistant_resp or '') > 500 else ''}")
        if notes:
            lines.append(f"\n**Notes:** {notes}")
        lines.append("\n---\n")

    return "\n".join(lines)


def export_conversations(conn) -> str:
    """Export all conversations with messages."""
    cursor = conn.cursor()

    # Get all conversations
    cursor.execute("""
        SELECT id, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
    """)
    conversations = cursor.fetchall()

    if not conversations:
        return "## Conversations\n\nNo conversations recorded yet.\n"

    lines = ["## Conversations\n"]
    lines.append(f"*{len(conversations)} conversations*\n")

    for conv_id, created_at, updated_at in conversations:
        # Get messages for this conversation
        cursor.execute("""
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conv_id,))
        messages = cursor.fetchall()

        if not messages:
            continue

        lines.append(f"### Conversation `{conv_id[:8]}...`")
        lines.append(f"**Started:** {created_at} | **Last activity:** {updated_at}")
        lines.append(f"**Messages:** {len(messages)}\n")

        for role, content, msg_time in messages:
            prefix = "**User:**" if role == "user" else "**Assistant:**"
            # Truncate very long messages
            display_content = content[:1000] + "..." if len(content) > 1000 else content
            lines.append(f"{prefix} {display_content}\n")

        lines.append("---\n")

    return "\n".join(lines)


def export_stats(conn) -> str:
    """Export basic statistics."""
    cursor = conn.cursor()

    # Count conversations
    cursor.execute("SELECT COUNT(*) FROM conversations")
    conv_count = cursor.fetchone()[0]

    # Count messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]

    # Count feedback
    cursor.execute("SELECT COUNT(*) FROM feedback")
    fb_count = cursor.fetchone()[0]

    # Feedback by type
    cursor.execute("""
        SELECT feedback_type, COUNT(*)
        FROM feedback
        GROUP BY feedback_type
    """)
    fb_by_type = cursor.fetchall()

    # Check if analytics table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='analytics'
    """)
    has_analytics = cursor.fetchone() is not None

    lines = ["## Statistics\n"]
    lines.append(f"- **Total conversations:** {conv_count}")
    lines.append(f"- **Total messages:** {msg_count}")
    lines.append(f"- **Feedback entries:** {fb_count}")

    if fb_by_type:
        lines.append("\n**Feedback breakdown:**")
        for fb_type, count in fb_by_type:
            lines.append(f"  - {fb_type}: {count}")

    if has_analytics:
        try:
            cursor.execute("SELECT COUNT(*) FROM analytics WHERE event_type = 'visit'")
            visit_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics WHERE event_type = 'message'")
            message_events = cursor.fetchone()[0]
            lines.append(f"\n**Analytics:**")
            lines.append(f"  - Page visits: {visit_count}")
            lines.append(f"  - Messages sent: {message_events}")
        except Exception:
            pass  # Analytics table may not have data yet

    lines.append("")
    return "\n".join(lines)


def main():
    """Main export function."""
    conn = get_connection()
    if not conn:
        return

    try:
        # Build the markdown content
        content = [
            "# AI Digital Twin - Data Export",
            f"\n*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "---\n",
            export_stats(conn),
            "---\n",
            export_feedback(conn),
            "---\n",
            export_conversations(conn),
        ]

        # Write to file
        OUTPUT_PATH.write_text("\n".join(content), encoding="utf-8")
        print(f"Exported to {OUTPUT_PATH}")
        print(f"File size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
