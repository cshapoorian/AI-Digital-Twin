"""
LLM client module for Groq API integration.

Uses Groq's free tier for fast inference with open-source models.
Loads configuration from backend/config/ directory.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from groq import Groq


# Engagement instructions - placed last in system prompt for maximum weight
ENGAGEMENT_PROMPT = """
FIRST MESSAGE FORMAT (MANDATORY):

When this is the first message in a conversation, your response MUST end by asking who they are and what brings them here. This applies even if they ask a question first.

CORRECT EXAMPLES:
- User: "hey" → "Hey! Who am I chatting with, and what brings you by?"
- User: "what do you do?" → "I'm a software engineer focused on test automation and AI. Who am I talking to, and what brings you here?"
- User: "what languages do you know?" → "Python, JavaScript, TypeScript, and a few others. What's your name and what brings you by?"

INCORRECT (never do this on first message):
- User: "what do you do?" → "I'm a software engineer with experience in..." (missing the question!)

Keep initial answers brief (1-2 sentences) to make room for asking about them. After you learn who they are, respond naturally without asking in every message.
""".strip()


def load_config():
    """Load settings from config/settings.txt file."""
    config_path = Path(__file__).parent.parent / "config" / "settings.txt"
    settings = {
        "temperature": 0.7,
        "max_tokens": 500,
        "history_limit": 20,
        "rag_top_k": 3,
        "rag_min_similarity": 0.1,
        "additional_instructions": ""
    }

    if config_path.exists():
        try:
            content = config_path.read_text(encoding="utf-8")
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in settings:
                        # Convert to appropriate type
                        if key in ["temperature", "rag_min_similarity"]:
                            settings[key] = float(value)
                        elif key in ["max_tokens", "history_limit", "rag_top_k"]:
                            settings[key] = int(value)
                        else:
                            settings[key] = value
        except Exception as e:
            print(f"Error loading config: {e}")

    return settings


def load_system_prompt():
    """Load system prompt from config/system_prompt.txt file."""
    prompt_path = Path(__file__).parent.parent / "config" / "system_prompt.txt"

    if prompt_path.exists():
        try:
            return prompt_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"Error loading system prompt: {e}")

    # Fallback default
    return """You are an AI digital twin representing the owner of this website.
Be friendly, conversational, and authentic. Share information about yourself openly."""


class LLMClient:
    """
    Client for interacting with Groq's LLM API.
    Handles prompt construction and response generation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: Groq API key. Defaults to GROQ_API_KEY env var.
            model: Model to use. Defaults to LLM_MODEL env var or llama-3.1-8b-instant.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Get a free key at https://console.groq.com"
            )

        self.model = model or os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        self.client = Groq(api_key=self.api_key)

        # Load config on init
        self.config = load_config()
        self.system_prompt = load_system_prompt()

    def generate(
        self,
        user_message: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None,
        personality_prompt: str = None,
        guardrail_prompt: str = "",
        identity_context: str = "",
        max_tokens: int = None,
        temperature: float = None,
        is_first_message: bool = False
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            user_message: The user's current message
            context: Relevant context from RAG retrieval
            conversation_history: Previous messages in the conversation
            personality_prompt: Custom personality instructions (uses config if None)
            guardrail_prompt: Safety/boundary instructions
            identity_context: Identity-based tone instructions (for known friends/family)
            max_tokens: Maximum response length (uses config if None)
            temperature: Creativity level (uses config if None)
            is_first_message: Whether this is the first message in the conversation

        Returns:
            The generated response text
        """
        # Use config values if not specified
        max_tokens = max_tokens or self.config["max_tokens"]
        temperature = temperature or self.config["temperature"]

        # Build system prompt
        system_content = self._build_system_prompt(
            personality_prompt or self.system_prompt,
            guardrail_prompt,
            context,
            identity_context,
            is_first_message
        )

        # Build messages array
        messages = [{"role": "system", "content": system_content}]

        # Add conversation history (if any)
        if conversation_history:
            history_limit = self.config["history_limit"]
            recent_history = conversation_history[-history_limit:]
            messages.extend(recent_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Call Groq API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            response_text = response.choices[0].message.content

            # For first messages, append the question if the model didn't include it
            if is_first_message and response_text:
                # Check if response already asks who they are
                lower_response = response_text.lower()
                has_who_question = any(phrase in lower_response for phrase in [
                    "who am i talking to",
                    "who am i chatting with",
                    "who are you",
                    "what's your name",
                    "what brings you",
                    "what brings you here",
                    "what brings you by"
                ])
                if not has_who_question:
                    response_text = response_text.rstrip() + " Who am I talking to, and what brings you here?"

            return response_text

        except Exception as e:
            print(f"LLM API error: {e}")
            return (
                "I'm having a bit of trouble responding right now. "
                "Could you try asking again?"
            )

    def _build_system_prompt(
        self,
        personality: str,
        guardrails: str,
        context: str,
        identity_context: str = "",
        is_first_message: bool = False
    ) -> str:
        """
        Construct the full system prompt.

        Args:
            personality: Personality and style instructions
            guardrails: Safety boundaries
            context: Retrieved context from training data
            identity_context: Dynamic tone instructions for recognized users
            is_first_message: Whether this is the first message in conversation

        Returns:
            Complete system prompt string
        """
        parts = [personality.strip()]

        if guardrails:
            parts.append(guardrails.strip())

        if context:
            parts.append(
                f"RELEVANT INFORMATION ABOUT YOU:\n{context}\n\n"
                "Use this information to answer questions when relevant. "
                "Don't mention that you're retrieving or looking up information - "
                "just share it naturally as if you know it."
            )

        # Add identity context for recognized friends/family (enables relaxed tone)
        if identity_context:
            parts.append(identity_context)

        # Add any additional instructions from config
        additional = self.config.get("additional_instructions", "")
        if additional:
            parts.append(additional)

        # Add engagement instructions LAST for maximum weight
        parts.append(ENGAGEMENT_PROMPT)

        return "\n\n".join(parts)

    def reload_config(self):
        """Reload configuration from files. Call after editing config files."""
        self.config = load_config()
        self.system_prompt = load_system_prompt()

    def health_check(self) -> bool:
        """
        Verify the API connection is working.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
