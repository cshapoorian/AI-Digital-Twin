"""
Guardrails module for content filtering.

Ensures responses are appropriate by:
1. Blocking sensitive topics (politics, controversy, etc.)
2. Filtering inappropriate language
3. Detecting when the model lacks information
"""

import re
from typing import Tuple, Optional


class GuardrailsFilter:
    """
    Content filter that validates both input queries and output responses.
    Provides both blocking and soft warnings.
    """

    # Topics to avoid - will trigger deflection
    BLOCKED_TOPICS = [
        # Political terms
        r"\b(democrat|republican|liberal|conservative|trump|biden|election|vote|voting)\b",
        r"\b(left.?wing|right.?wing|socialism|capitalism|communist|fascist)\b",
        r"\b(abortion|pro.?life|pro.?choice)\b",
        r"\b(gun control|second amendment|2nd amendment)\b",

        # Controversial topics
        r"\b(religion|religious|atheist|christian|muslim|jewish|hindu|buddhist)\b",
        r"\b(immigration|immigrant|illegal alien|border wall|deportation)\b",
        r"\b(racism|racist|sexism|sexist|homophob|transphob)\b",

        # Sensitive personal topics
        r"\b(salary|income|net worth|how much.*make|how much.*earn)\b",
        r"\b(address|where.*live|phone number|social security)\b",
    ]

    # Inappropriate content patterns
    INAPPROPRIATE_PATTERNS = [
        r"\b(fuck|shit|damn|ass|bitch|bastard)\b",
        r"\b(kill|murder|suicide|self.?harm)\b",
        r"\b(hate|hatred)\s+(you|them|him|her|everyone)\b",
    ]

    # Phrases indicating lack of knowledge
    UNCERTAINTY_INDICATORS = [
        "i don't know",
        "i'm not sure",
        "i cannot answer",
        "i don't have information",
        "i can't help with",
        "outside my knowledge",
        "beyond my understanding",
    ]

    # Default deflection response
    DEFLECTION_RESPONSE = (
        "I'd prefer to keep our conversation focused on topics I'm comfortable discussing. "
        "Feel free to ask me about my hobbies, work, interests, or other aspects of who I am!"
    )

    def __init__(self):
        """Initialize compiled regex patterns for efficiency."""
        self._blocked_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.BLOCKED_TOPICS
        ]
        self._inappropriate_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.INAPPROPRIATE_PATTERNS
        ]

    def check_input(self, user_message: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user input should be blocked.

        Args:
            user_message: The user's message

        Returns:
            Tuple of (is_allowed, deflection_message)
            If is_allowed is True, deflection_message is None.
            If is_allowed is False, deflection_message contains the response to send.
        """
        # Check for blocked topics
        for pattern in self._blocked_patterns:
            if pattern.search(user_message):
                return False, self.DEFLECTION_RESPONSE

        # Check for inappropriate content
        for pattern in self._inappropriate_patterns:
            if pattern.search(user_message):
                return False, (
                    "I'd appreciate if we could keep the conversation respectful. "
                    "What else would you like to know about me?"
                )

        return True, None

    def check_output(self, response: str) -> Tuple[bool, str]:
        """
        Validate and potentially modify the model's response.

        Args:
            response: The LLM's generated response

        Returns:
            Tuple of (is_valid, final_response)
            If is_valid is True, final_response is the original or cleaned response.
            If is_valid is False, final_response is a fallback.
        """
        # Check for blocked topics in response (model might have slipped)
        for pattern in self._blocked_patterns:
            if pattern.search(response):
                return False, self.DEFLECTION_RESPONSE

        # Check for inappropriate language in response
        for pattern in self._inappropriate_patterns:
            if pattern.search(response):
                # Try to clean the response rather than block entirely
                cleaned = pattern.sub("[...]", response)
                return True, cleaned

        return True, response

    def detect_uncertainty(self, response: str) -> bool:
        """
        Detect if the response indicates the model lacks information.
        Useful for logging questions to improve training data.

        Args:
            response: The LLM's generated response

        Returns:
            True if the response indicates uncertainty
        """
        response_lower = response.lower()
        for indicator in self.UNCERTAINTY_INDICATORS:
            if indicator in response_lower:
                return True
        return False

    def get_system_prompt_guardrails(self) -> str:
        """
        Returns guardrail instructions to include in the system prompt.
        This provides an additional layer of protection via prompt engineering.
        """
        return """
IMPORTANT BOUNDARIES:
- Do NOT discuss politics, elections, political parties, or controversial political topics
- Do NOT share opinions on religion or religious practices
- Do NOT discuss sensitive social issues like abortion, gun control, or immigration policy
- Do NOT reveal personal information like address, phone number, or financial details
- If asked about these topics, politely decline and redirect to other topics
- Keep responses friendly, professional, and focused on sharing who you are as a person
- If you don't have information to answer a question, say so honestly
"""
