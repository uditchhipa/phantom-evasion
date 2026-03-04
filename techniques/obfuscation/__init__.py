"""Phantom Evasion - Obfuscation techniques."""

from techniques.obfuscation.string_obfuscate import generate_string_obfuscation
from techniques.obfuscation.junk_code import generate_junk_code
from techniques.obfuscation.polymorphic import generate_polymorphic_code
from techniques.obfuscation.control_flow_flatten import generate_control_flow_flattening
from techniques.obfuscation.string_encrypt_stack import generate_string_encrypt_stack

__all__ = [
    "generate_string_obfuscation",
    "generate_junk_code",
    "generate_polymorphic_code",
    "generate_control_flow_flattening",
    "generate_string_encrypt_stack",
]
