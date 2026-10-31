
"""Gemma 4 frame analysis through the hosted Gemini API."""

import json
import logging
import re
import time
from dataclasses import dataclass, field

from django.conf import settings

logger = logging.getLogger(__name__)

PROMPT = """
You are analysing a sampled frame from recorded CCTV footage.

Describe only what is visibly present.
Identify visible people in non-identifying terms.
Describe visible objects, observable actions, and environmental context.

Do not:
- Identify people or infer their identities.
- Guess intentions.
- Invent events that are not visible.
- Make assumptions about what happened before or after this frame.

If something is unclear, explicitly state that it is unclear.

Return ONLY valid JSON using exactly this structure:

{
    "description": "A concise description of the frame",
    "visible_objects": ["object 1", "object 2"],
    "visible_actions": ["observable action 1"]
}
"""


class AIServiceError(Exception):
    """Temporary or per-frame AI failure."""


class AIFatalError(AIServiceError):
    """Invalid API configuration or request."""


class AIRateLimitError(AIServiceError):
    """Gemini API quota or rate limit exceeded."""


class AIInvalidResponse(AIServiceError):
    """Model returned an unusable response."""


@dataclass
class FrameAnalysis:
    description: str
    visible_objects: list = field(default_factory=list)
    visible_actions: list = field(default_factory=list)
    confidence: float | None = None


def _str_list(value, cap=30):
    if not isinstance(value, list):
        return []

    return [
        item.strip()[:100]
        for item in value
        if isinstance(item, str) and item.strip()
    ][:cap]


def parse_model_output(text: str) -> FrameAnalysis:
    """Parse and validate the model's JSON response."""

    if not text or not text.strip():
        raise AIInvalidResponse("Gemma returned an empty response.")

    # Support JSON wrapped in Markdown code fences.
    match = re.search(r"\{.*\}", text, re.S)

    if not match:
        raise AIInvalidResponse(
            f"No JSON object found in response: {text[:300]}"
        )

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as error:
        raise AIInvalidResponse(
            f"Invalid JSON returned by Gemma: {error.msg}"
        ) from error

    if not isinstance(data, dict):
        raise AIInvalidResponse("Gemma response must be a JSON object.")

    description = data.get("description")

    if not isinstance(description, str) or not description.strip():
        raise AIInvalidResponse(
            "Gemma response does not contain a valid description."
        )

    confidence = data.get("confidence")

    if (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and 0 <= confidence <= 1
    ):
        confidence = float(confidence)
    else:
        confidence = None

    return FrameAnalysis(
        description=description.strip()[:2000],
        visible_objects=_str_list(data.get("visible_objects")),
        visible_actions=_str_list(data.get("visible_actions")),
        confidence=confidence,
    )


def _sleep(seconds):
    """Separate function so tests can patch it."""
    time.sleep(seconds)


class GeminiService:

    def __init__(
        self,
        api_key=None,
        model=None,
        timeout=None,
        max_retries=None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMMA_MODEL
        self.timeout = timeout or settings.GEMINI_TIMEOUT_SECONDS

        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.GEMINI_MAX_RETRIES
        )

        if not self.api_key:
            raise AIFatalError(
                "GEMINI_API_KEY is not configured on the server."
            )

        if not self.model:
            raise AIFatalError(
                "GEMMA_MODEL is not configured on the server."
            )

        self._client = None

    @property
    def client(self):
        """Create the Gemini client only when needed."""

        if self._client is None:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(
                    timeout=int(self.timeout * 1000)
                ),
            )

        return self._client

    def _generate(self, jpeg: bytes) -> str:
        """Send one JPEG frame to Gemma 4."""

        if not jpeg:
            raise ValueError("Empty JPEG frame received.")

        if not isinstance(jpeg, bytes):
            raise ValueError("Frame must be provided as bytes.")

        if not jpeg.startswith(b"\xff\xd8\xff"):
            raise ValueError(
                "Invalid JPEG image received from frame extractor."
            )

        from google.genai import types

        image_part = types.Part.from_bytes(
            data=jpeg,
            mime_type="image/jpeg",
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                image_part,
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
            ),
        )

        if not response.text:
            raise AIInvalidResponse(
                "Gemma returned no text for the supplied frame."
            )

        logger.info(
            "Gemma successfully analysed a frame using model %s",
            self.model,
        )

        return response.text

    def analyze_frame(self, jpeg: bytes) -> FrameAnalysis:
        """Analyse one frame with retries and useful error logging."""

        from google.genai import errors

        last_error = None

        for attempt in range(self.max_retries + 1):

            try:
                response_text = self._generate(jpeg)

                return parse_model_output(response_text)

            except AIInvalidResponse as error:
                last_error = error

                logger.warning(
                    "Invalid Gemma response on attempt %s: %s",
                    attempt + 1,
                    error,
                )

            except errors.APIError as error:
                code = getattr(error, "code", None)

                logger.exception(
                    "Gemini API request failed. HTTP status: %s",
                    code,
                )

                if code in (400, 401, 403, 404):
                    raise AIFatalError(
                        f"Gemini rejected the request. "
                        f"HTTP {code}. Check the model ID, API key, "
                        f"and image request."
                    ) from error

                if code == 429:
                    last_error = AIRateLimitError(
                        "Gemini API quota or rate limit exceeded."
                    )
                else:
                    last_error = AIServiceError(
                        f"Gemini API error: HTTP {code}: {error}"
                    )

            except Exception as error:
                last_error = AIServiceError(
                    f"Gemini request failed: "
                    f"{type(error).__name__}: {error}"
                )

                logger.exception(
                    "Gemini request failed on attempt %s",
                    attempt + 1,
                )

            if attempt < self.max_retries:
                delay = min(2 ** attempt, 20)

                logger.info(
                    "Retrying Gemini request in %s seconds.",
                    delay,
                )

                _sleep(delay)

        raise last_error


def get_analyzer():
    """Return a configured Gemini analysis service."""
    return GeminiService()
