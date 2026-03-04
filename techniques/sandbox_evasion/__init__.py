"""Phantom Evasion - Sandbox evasion techniques."""

from techniques.sandbox_evasion.sleep_encrypt import generate_sleep_encrypt
from techniques.sandbox_evasion.env_checks import generate_env_checks
from techniques.sandbox_evasion.parent_spoof import generate_parent_spoof
from techniques.sandbox_evasion.delayed_exec import generate_delayed_exec
from techniques.sandbox_evasion.resource_check import generate_resource_check

__all__ = [
    "generate_sleep_encrypt",
    "generate_env_checks",
    "generate_parent_spoof",
    "generate_delayed_exec",
    "generate_resource_check",
]
