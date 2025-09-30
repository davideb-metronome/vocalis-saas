"""
Public entry point for the Metronome client instance (SDK-only).
"""

from .sdk_client import SdkMetronomeClient

# Backwards-compatible exported name used across the codebase
metronome_client = SdkMetronomeClient()
