"""Runtime configuration for the Adaptive Advisory backend.

All settings are read from the environment so the same image runs locally,
in Cloud Run and in CI without modification.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    # --- Server -----------------------------------------------------------
    port: int = int(os.getenv("PORT", "8080"))
    static_dir: str = os.getenv("STATIC_DIR", "static")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    allowed_origins: list[str] = field(default_factory=lambda: _csv("ALLOWED_ORIGINS"))

    # --- Vertex AI / Gemini ----------------------------------------------
    # Vertex AI is the default transport, reached with Application Default
    # Credentials. Set USE_VERTEX_AI=false together with GOOGLE_API_KEY to
    # develop against the AI Studio endpoint instead.
    use_vertex_ai: bool = _flag("USE_VERTEX_AI", True)
    project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # Live model id. Vertex and AI Studio use different identifiers and these
    # move quickly while the Live API is in preview, so keep it configurable.
    model: str = os.getenv("GEMINI_LIVE_MODEL", "gemini-live-2.5-flash-native-audio")

    # --- Voice / locale ---------------------------------------------------
    # The demo targets the German market: German prompts, German UI copy,
    # de-DE speech in and out.
    language_code: str = os.getenv("LIVE_LANGUAGE_CODE", "de-DE")
    voice_name: str = os.getenv("LIVE_VOICE_NAME", "Aoede")

    # --- Audio ------------------------------------------------------------
    input_sample_rate: int = int(os.getenv("INPUT_SAMPLE_RATE", "16000"))
    output_sample_rate: int = int(os.getenv("OUTPUT_SAMPLE_RATE", "24000"))

    # --- Behaviour --------------------------------------------------------
    affective_dialog: bool = _flag("LIVE_AFFECTIVE_DIALOG", True)
    proactive_audio: bool = _flag("LIVE_PROACTIVE_AUDIO", False)
    session_idle_timeout_s: int = int(os.getenv("SESSION_IDLE_TIMEOUT_S", "900"))

    def validate(self) -> list[str]:
        """Returns a list of human readable configuration problems."""
        problems: list[str] = []
        if self.use_vertex_ai:
            if not self.project:
                problems.append(
                    "GOOGLE_CLOUD_PROJECT is not set but USE_VERTEX_AI is enabled."
                )
            if not self.location:
                problems.append("GOOGLE_CLOUD_LOCATION is not set.")
        elif not self.api_key:
            problems.append(
                "GOOGLE_API_KEY is not set and USE_VERTEX_AI is disabled."
            )
        return problems


    def apply_to_environment(self) -> None:
        """Publishes the settings ADK reads from the environment.

        ADK constructs its own google-genai client, configured by
        ``GOOGLE_GENAI_USE_VERTEXAI`` and friends rather than by constructor
        arguments. Setting them here keeps one source of truth and means a
        `.env` file works the same as Cloud Run env vars.
        """
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1" if self.use_vertex_ai else "0"
        if self.use_vertex_ai:
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", self.project)
            os.environ.setdefault("GOOGLE_CLOUD_LOCATION", self.location)
        elif self.api_key:
            os.environ.setdefault("GOOGLE_API_KEY", self.api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
