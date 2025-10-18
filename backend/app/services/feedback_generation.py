"""
Feedback Generation Service

Converts technical pose comparison data into human-readable feedback using LLM.
This service is called AFTER dance sections complete (batch processing, not real-time).
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.data.config import settings


class FeedbackGenerationService:
    """
    Service for generating AI-powered dance feedback.

    Takes technical error data (angles, positions) and converts them into
    friendly, actionable feedback using OpenAI's GPT models.
    """

    def __init__(self):
        """Initialize the OpenAI client with settings from config."""
        if not settings.openai_api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file"
            )

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    def generate_feedback(
        self,
        problem_segments: List[Dict[str, Any]],
        max_items: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate feedback for detected problem segments.

        Args:
            problem_segments: List of problem segments with technical error data.
                Each segment should have:
                - timestamp_start: float
                - timestamp_end: float
                - errors: List of error dictionaries with body_part, expected, actual, difference
                - accuracy: float (0-1)
            max_items: Maximum number of feedback items to generate (uses config default if None)

        Returns:
            List of feedback dictionaries with:
            - timestamp: float (midpoint of segment)
            - title: str (brief description)
            - feedback: str (actionable advice)
            - severity: str ("high", "medium", "low")
            - body_parts: List[str]
        """
        max_items = max_items or settings.max_feedback_items_per_section

        # Limit to most significant problems
        sorted_segments = sorted(
            problem_segments,
            key=lambda x: x.get('accuracy', 1.0)  # Lower accuracy = bigger problem
        )[:max_items]

        feedback_items = []

        for segment in sorted_segments:
            try:
                feedback_item = self._generate_single_feedback(segment)
                feedback_items.append(feedback_item)
            except Exception as e:
                # Fallback to template-based feedback if LLM fails
                feedback_items.append(self._generate_fallback_feedback(segment))
                print(f"LLM feedback generation failed: {e}. Using fallback.")

        return feedback_items

    def _generate_single_feedback(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate feedback for a single problem segment using LLM.

        Args:
            segment: Problem segment data with errors and timing

        Returns:
            Feedback dictionary
        """
        # Construct the prompt with structured error data
        prompt = self._build_prompt(segment)

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly and encouraging K-pop dance instructor. "
                        "Your job is to help students improve their dance technique by "
                        "providing specific, actionable feedback based on technical error data. "
                        "Keep feedback conversational, positive, and under 100 words."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        feedback_text = response.choices[0].message.content.strip()

        # Extract body parts and determine severity
        body_parts = list(set(
            error.get('body_part', 'unknown')
            for error in segment.get('errors', [])
        ))

        severity = self._calculate_severity(segment)

        # Calculate midpoint timestamp for the feedback
        timestamp = (
            segment.get('timestamp_start', 0) + segment.get('timestamp_end', 0)
        ) / 2

        return {
            "timestamp": timestamp,
            "title": self._generate_title(segment),
            "feedback": feedback_text,
            "severity": severity,
            "body_parts": body_parts
        }

    def _build_prompt(self, segment: Dict[str, Any]) -> str:
        """
        Build the LLM prompt from technical error data.

        Args:
            segment: Problem segment with error data

        Returns:
            Formatted prompt string
        """
        timestamp_start = segment.get('timestamp_start', 0)
        timestamp_end = segment.get('timestamp_end', 0)
        errors = segment.get('errors', [])
        accuracy = segment.get('accuracy', 0.0)

        prompt = f"""A student just attempted a K-pop dance move from {timestamp_start:.1f}s to {timestamp_end:.1f}s.
Their overall accuracy for this segment was {accuracy*100:.1f}%.

Technical errors detected:
"""

        for error in errors:
            body_part = error.get('body_part', 'unknown')
            expected = error.get('expected', 'N/A')
            actual = error.get('actual', 'N/A')
            difference = error.get('difference', 'N/A')

            prompt += f"- {body_part}: expected {expected}, got {actual} (difference: {difference})\n"

        prompt += """
Generate friendly, actionable feedback:
1. What went wrong (in plain English, not technical terms)
2. Why it matters for the choreography
3. Specific correction steps
4. Brief encouragement

Keep it conversational and under 100 words."""

        return prompt

    def _generate_fallback_feedback(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate template-based feedback if LLM fails.

        Args:
            segment: Problem segment data

        Returns:
            Feedback dictionary using templates
        """
        errors = segment.get('errors', [])
        timestamp = (
            segment.get('timestamp_start', 0) + segment.get('timestamp_end', 0)
        ) / 2

        # Simple template-based feedback
        if errors:
            primary_error = errors[0]
            body_part = primary_error.get('body_part', 'body position')
            difference = primary_error.get('difference', 'off')

            feedback_text = (
                f"Your {body_part} needs adjustment. "
                f"Try to match the reference position more closely. "
                f"The difference was {difference}. Keep practicing!"
            )
        else:
            feedback_text = "Keep working on matching the reference pose more closely."

        body_parts = list(set(
            error.get('body_part', 'unknown')
            for error in errors
        ))

        return {
            "timestamp": timestamp,
            "title": self._generate_title(segment),
            "feedback": feedback_text,
            "severity": self._calculate_severity(segment),
            "body_parts": body_parts
        }

    def _generate_title(self, segment: Dict[str, Any]) -> str:
        """
        Generate a brief title for the feedback item.

        Args:
            segment: Problem segment data

        Returns:
            Title string
        """
        timestamp_start = segment.get('timestamp_start', 0)
        errors = segment.get('errors', [])

        if errors:
            primary_body_part = errors[0].get('body_part', 'Position').replace('_', ' ').title()
            return f"{primary_body_part} at {timestamp_start:.1f}s"

        return f"Movement at {timestamp_start:.1f}s"

    def _calculate_severity(self, segment: Dict[str, Any]) -> str:
        """
        Calculate severity level based on accuracy and error magnitude.

        Args:
            segment: Problem segment data

        Returns:
            Severity level: "high", "medium", or "low"
        """
        accuracy = segment.get('accuracy', 1.0)

        if accuracy < 0.5:
            return "high"
        elif accuracy < 0.7:
            return "medium"
        else:
            return "low"


# Factory function to get service instance
def get_feedback_service() -> FeedbackGenerationService:
    """
    Get or create the feedback generation service.

    Returns:
        FeedbackGenerationService instance
    """
    return FeedbackGenerationService()
