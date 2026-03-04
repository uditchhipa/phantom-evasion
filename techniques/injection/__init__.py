"""Phantom Evasion - Injection techniques."""

from techniques.injection.classic_injection import generate_classic_injection
from techniques.injection.apc_injection import generate_apc_injection
from techniques.injection.early_bird import generate_early_bird_injection
from techniques.injection.callback_injection import generate_callback_injection
from techniques.injection.thread_hijack import generate_thread_hijack
from techniques.injection.fiber_injection import generate_fiber_injection

__all__ = [
    "generate_classic_injection",
    "generate_apc_injection",
    "generate_early_bird_injection",
    "generate_callback_injection",
    "generate_thread_hijack",
    "generate_fiber_injection",
]
