"""
Phantom Evasion - Payload Loader

LEGAL DISCLAIMER:
For authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Any

# Maximum permitted shellcode size (10 MB)
_MAX_SHELLCODE_BYTES = 10 * 1024 * 1024

_BINARY_EXTENSIONS = {".bin", ".raw"}
_HEX_EXTENSIONS = {".txt", ".hex"}


class PayloadLoader:
    """Load and validate raw shellcode/payloads from various file formats."""

    def load(self, path: str) -> Dict[str, Any]:
        """Load shellcode from *path* and return a metadata dictionary.

        The returned dict contains:
            - ``shellcode`` (bytes): raw shellcode bytes
            - ``size`` (int): number of bytes
            - ``sha256`` (str): hex-encoded SHA-256 digest
            - ``type`` (str): ``"binary"`` or ``"hex-encoded"``

        Supported file extensions:
            - ``.bin``, ``.raw`` → raw binary
            - ``.txt``, ``.hex`` → hex-encoded text (whitespace is stripped)

        Raises:
            FileNotFoundError: if *path* does not exist.
            ValueError: if the file is empty, too large, or contains invalid hex.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Payload file not found: {path}")

        ext = file_path.suffix.lower()
        if ext in _BINARY_EXTENSIONS:
            shellcode = self._load_binary(file_path)
            sc_type = "binary"
        elif ext in _HEX_EXTENSIONS:
            shellcode = self._load_hex(file_path)
            sc_type = "hex-encoded"
        else:
            # Unknown extension – attempt binary load and fall back to hex
            try:
                shellcode = self._load_binary(file_path)
                sc_type = "binary (auto-detected)"
            except Exception:
                shellcode = self._load_hex(file_path)
                sc_type = "hex-encoded (auto-detected)"

        if not self._validate(shellcode):
            raise ValueError(
                f"Payload validation failed: size={len(shellcode)} bytes "
                f"(max {_MAX_SHELLCODE_BYTES // (1024 * 1024)} MB, min 1 byte)"
            )

        digest = hashlib.sha256(shellcode).hexdigest()

        return {
            "shellcode": shellcode,
            "size": len(shellcode),
            "sha256": digest,
            "type": sc_type,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_binary(self, path: Path) -> bytes:
        """Read a raw binary file and return its contents."""
        with open(path, "rb") as f:
            return f.read()

    def _load_hex(self, path: Path) -> bytes:
        """Read a hex-encoded text file and decode it to bytes.

        Accepts both continuous hex strings (e.g. ``deadbeef``) and
        whitespace/comma separated byte literals (e.g. ``\\x90, \\x90``).
        """
        with open(path, "r", errors="replace") as f:
            raw_text = f.read()

        # Strip common decorators: \x, 0x, commas, spaces, newlines
        cleaned = (
            raw_text
            .replace("\\x", "")
            .replace("0x", "")
            .replace(",", "")
            .replace(" ", "")
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )

        try:
            return bytes.fromhex(cleaned)
        except ValueError as exc:
            raise ValueError(f"Invalid hex-encoded payload: {exc}") from exc

    def _validate(self, shellcode: bytes) -> bool:
        """Return True if *shellcode* is non-empty and within the size limit."""
        return 0 < len(shellcode) <= _MAX_SHELLCODE_BYTES
