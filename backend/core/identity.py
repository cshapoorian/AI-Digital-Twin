"""
Identity detection module for friend/family recognition.

Parses known persons from training data and detects when users identify
themselves in conversation. Enables relaxed tone for recognized individuals.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IdentityMatch:
    """Represents a detected identity match."""
    name: str
    relationship: str  # "family", "partner", "friend"
    relationship_detail: str  # "sister", "brother", "Colorado friend", etc.
    is_known: bool = True


class IdentityDetector:
    """
    Detects when users identify themselves as known friends or family.
    Loads names from family_and_friends.txt and scans conversation history.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the identity detector.

        Args:
            data_dir: Path to data directory. Defaults to backend/data.
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data"

        self.known_persons: Dict[str, Tuple[str, str]] = {}  # name -> (relationship, detail)
        self._load_known_persons()

    def _load_known_persons(self):
        """Parse names from family_and_friends.txt into the known_persons dict."""
        file_path = self.data_dir / "family_and_friends.txt"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            self._parse_family_members(content)
            self._parse_partner(content)
            self._parse_friends(content)
        except Exception as e:
            print(f"Error loading known persons: {e}")

    def _parse_family_members(self, content: str):
        """Extract family member names from content."""
        # Pattern: "sister, her name is [Name]" or "brother, his name is [Name]"
        # Also: "dad's name is [Name]", "mom's name is [Name]"
        patterns = [
            (r"younger sister.*?name is (\w+)", "family", "sister"),
            (r"older brother.*?name is (\w+)", "family", "brother"),
            (r"dad'?s? name is (\w+)", "family", "dad"),
            (r"mom'?s? name is (\w+)", "family", "mom"),
        ]

        for pattern, relationship, detail in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                self.known_persons[name.lower()] = (relationship, detail)

    def _parse_partner(self, content: str):
        """Extract partner name(s) from content."""
        # Pattern: "girlfriend's name is Brianna or Bri"
        match = re.search(
            r"girlfriend'?s? name is (\w+)(?: or (\w+))?",
            content,
            re.IGNORECASE
        )
        if match:
            name = match.group(1).strip()
            self.known_persons[name.lower()] = ("partner", "girlfriend")
            if match.group(2):
                nickname = match.group(2).strip()
                self.known_persons[nickname.lower()] = ("partner", "girlfriend")

    def _parse_friends(self, content: str):
        """Extract friend names from content."""
        # Pattern: "Colorado Friends: name1, name2, ..."
        friend_patterns = [
            (r"Colorado Friends?:\s*([^\n]+)", "Colorado friend"),
            (r"California Friends?:\s*([^\n]+)", "California friend"),
        ]

        for pattern, detail in friend_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                names_str = match.group(1)
                # Handle parenthetical notes like "Cam (call him cami jon if...)"
                names_str = re.sub(r'\([^)]*\)', '', names_str)
                names = [n.strip() for n in names_str.split(',') if n.strip()]
                for name in names:
                    # Handle multi-word names by taking first word
                    first_name = name.split()[0] if name else name
                    if first_name:
                        self.known_persons[first_name.lower()] = ("friend", detail)

    def detect_identity(
        self,
        conversation_history: List[Dict[str, str]],
        current_message: str = ""
    ) -> Optional[IdentityMatch]:
        """
        Scan conversation for user self-identification.

        Args:
            conversation_history: List of {"role": "...", "content": "..."} messages
            current_message: The current user message to also check

        Returns:
            IdentityMatch if a known person is detected, None otherwise
        """
        # Combine all user messages to scan
        user_messages = [
            msg["content"]
            for msg in conversation_history
            if msg.get("role") == "user"
        ]
        if current_message:
            user_messages.append(current_message)

        all_text = " ".join(user_messages)

        # Patterns for self-identification
        id_patterns = [
            r"(?:i'?m|i am|this is|it'?s|it is)\s+(\w+)",  # "I'm Kyle", "This is Parisa"
            r"my name(?:'?s| is)\s+(\w+)",  # "My name is Kaleb"
            r"(\w+)\s+here",  # "Kaleb here"
            r"hey,?\s+it'?s\s+(\w+)",  # "Hey, it's Bri"
        ]

        for pattern in id_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                name = match.lower()
                if name in self.known_persons:
                    relationship, detail = self.known_persons[name]
                    return IdentityMatch(
                        name=match.capitalize(),
                        relationship=relationship,
                        relationship_detail=detail,
                        is_known=True
                    )

        return None

    def get_identity_prompt(self, identity: IdentityMatch) -> str:
        """
        Generate prompt context for a recognized identity.

        Args:
            identity: The detected IdentityMatch

        Returns:
            Prompt text to inject into the system prompt
        """
        relationship_desc = {
            "family": f"Cameron's {identity.relationship_detail}",
            "partner": "Cameron's girlfriend",
            "friend": f"Cameron's {identity.relationship_detail}",
        }.get(identity.relationship, "someone Cameron knows")

        return f"""IDENTITY CONTEXT: The user chatting with you has identified as {identity.name}, who is {relationship_desc}.
This means the person you're talking to right now IS {identity.name} - they're not a stranger, they're someone Cameron knows personally.

Since {identity.name} is {'family' if identity.relationship == 'family' else 'a close ' + identity.relationship}, you can be more relaxed:
- Use more casual language and slang freely
- Be playful, joke around more
- Don't hold back on expressions like "dude", "yo", "haha"
- Share more openly, be less guarded
- Match their energy - if they're hyped, get hyped with them
- Reference shared experiences or inside jokes from Cameron's data if relevant
- Remember: YOU are Cameron's digital voice, THEY are {identity.name} visiting"""

    def reload(self):
        """Reload known persons from disk."""
        self.known_persons = {}
        self._load_known_persons()
