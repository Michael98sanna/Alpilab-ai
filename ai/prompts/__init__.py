"""Prompt templates for Alpilab AI.

Keep prompts versioned and provider-agnostic. The application should
load templates from here instead of hard-coding strings near providers.
"""

from .technical import SYSTEM_TECHNICAL_ASSISTANT

__all__ = ["SYSTEM_TECHNICAL_ASSISTANT"]
