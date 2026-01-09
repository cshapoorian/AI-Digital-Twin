"""
AI Pipeline module - orchestrates the full response generation flow.

Flow: User Message -> Guardrails Check -> RAG Retrieval -> LLM Generation -> Output Validation
"""

from typing import List, Dict, Tuple, Optional
from core.rag import RAGRetriever
from core.llm import LLMClient
from core.guardrails import GuardrailsFilter
from core.identity import IdentityDetector


class ADTPipeline:
    """
    Orchestrates the AI Digital Twin response generation pipeline.
    Combines RAG retrieval, LLM generation, and guardrails filtering.
    """

    def __init__(
        self,
        data_dir: str = None,
        model: str = None,
        personality_prompt: str = None
    ):
        """
        Initialize the pipeline components.

        Args:
            data_dir: Path to training data directory
            model: LLM model to use
            personality_prompt: Custom personality instructions
        """
        self.rag = RAGRetriever(data_dir)
        self.llm = LLMClient(model=model) if model else LLMClient()
        self.guardrails = GuardrailsFilter()
        self.identity = IdentityDetector(data_dir)
        self.personality_prompt = personality_prompt

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Dict]:
        """
        Generate a response for the user's message.

        Args:
            user_message: The user's input message
            conversation_history: Previous messages in format [{"role": "...", "content": "..."}]

        Returns:
            Tuple of (response_text, metadata)
            Metadata includes: blocked, uncertainty_detected, context_used
        """
        metadata = {
            "blocked": False,
            "uncertainty_detected": False,
            "context_used": False,
            "deflection_reason": None,
            "identity_detected": None
        }

        # Step 0: Detect user identity for tone adjustment
        identity = self.identity.detect_identity(
            conversation_history or [],
            current_message=user_message
        )
        identity_context = ""
        if identity:
            identity_context = self.identity.get_identity_prompt(identity)
            metadata["identity_detected"] = {
                "name": identity.name,
                "relationship": identity.relationship
            }

        # Step 1: Check input with guardrails
        input_allowed, deflection = self.guardrails.check_input(user_message)
        if not input_allowed:
            metadata["blocked"] = True
            metadata["deflection_reason"] = "blocked_topic"
            return deflection, metadata

        # Step 2: Retrieve relevant context
        context = self.rag.get_context_string(user_message, top_k=3)
        if context:
            metadata["context_used"] = True

        # Step 3: Generate response with LLM
        # Detect if this is the first message (empty history = new conversation)
        is_first_message = not conversation_history or len(conversation_history) == 0

        response = self.llm.generate(
            user_message=user_message,
            context=context,
            conversation_history=conversation_history or [],
            personality_prompt=self.personality_prompt,
            guardrail_prompt=self.guardrails.get_system_prompt_guardrails(),
            identity_context=identity_context,
            is_first_message=is_first_message
        )

        # Step 4: Validate output with guardrails
        output_valid, final_response = self.guardrails.check_output(response)
        if not output_valid:
            metadata["blocked"] = True
            metadata["deflection_reason"] = "output_filtered"

        # Step 5: Check for uncertainty (for feedback logging)
        if self.guardrails.detect_uncertainty(final_response):
            metadata["uncertainty_detected"] = True

        return final_response, metadata

    def reload_training_data(self):
        """Reload training data from disk."""
        self.rag.reload()
        self.identity.reload()


# Module-level singleton for convenience
_pipeline: Optional[ADTPipeline] = None


def get_pipeline() -> ADTPipeline:
    """
    Get or create the singleton pipeline instance.
    Lazy initialization to allow configuration before first use.
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = ADTPipeline()
    return _pipeline


def generate_response(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None
) -> Tuple[str, Dict]:
    """
    Convenience function to generate a response using the default pipeline.

    Args:
        user_message: The user's input message
        conversation_history: Previous messages

    Returns:
        Tuple of (response_text, metadata)
    """
    pipeline = get_pipeline()
    return pipeline.generate_response(user_message, conversation_history)
