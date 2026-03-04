"""Phantom Evasion - EDR bypass techniques."""

from techniques.edr_bypass.direct_syscalls import generate_direct_syscalls
from techniques.edr_bypass.indirect_syscalls import generate_indirect_syscalls
from techniques.edr_bypass.unhook_ntdll import generate_unhook_ntdll
from techniques.edr_bypass.api_hashing import generate_api_hashing
from techniques.edr_bypass.hells_gate import generate_hells_gate
from techniques.edr_bypass.module_stomping import generate_module_stomping

__all__ = [
    "generate_direct_syscalls",
    "generate_indirect_syscalls",
    "generate_unhook_ntdll",
    "generate_api_hashing",
    "generate_hells_gate",
    "generate_module_stomping",
]
