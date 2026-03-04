"""
Phantom Evasion - Windows Defender Scanning Module

LEGAL DISCLAIMER:
For authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


# Candidate paths to the Windows Defender CLI binary
_DEFENDER_PATHS = [
    r"C:\Program Files\Windows Defender\MpCmdRun.exe",
    r"C:\Program Files\Windows Defender Advanced Threat Protection\MpCmdRun.exe",
]

# Wine wrapper path (Linux cross-platform testing)
_WINE_PATH = "/usr/bin/wine"


def _find_defender() -> Optional[str]:
    """Return the first usable path to MpCmdRun.exe, or None."""
    for path in _DEFENDER_PATHS:
        if os.path.isfile(path):
            return path
    return None


def _parse_defender_output(output: str) -> Dict[str, Any]:
    """Extract detection status and threat name from MpCmdRun output."""
    output_lower = output.lower()

    if ("no threats" in output_lower or
            ("scan finished" in output_lower and "threat" not in output_lower)):
        return {
            "detected": False,
            "threat_name": "",
            "status": "clean",
        }

    threat_match = re.search(r"threat name\s*:\s*(.+)", output, re.IGNORECASE)
    threat_name = threat_match.group(1).strip() if threat_match else "Unknown"

    if "threat" in output_lower or "detected" in output_lower or "infected" in output_lower:
        return {
            "detected": True,
            "threat_name": threat_name,
            "status": "detected",
        }

    return {
        "detected": False,
        "threat_name": "",
        "status": "unknown",
    }


def scan_with_defender(file_path: str) -> Dict[str, Any]:
    """Scan *file_path* with Windows Defender CLI (MpCmdRun.exe).

    On non-Windows hosts this function attempts to use Wine to invoke the
    Windows Defender binary, or returns a ``status: unavailable`` result.

    Args:
        file_path: Absolute or relative path to the file to scan.

    Returns:
        Dict with keys:
            - ``detected``    (bool)  – True if a threat was detected.
            - ``threat_name`` (str)   – Threat name reported by Defender.
            - ``status``      (str)   – ``"clean"`` | ``"detected"`` |
                                        ``"unavailable"`` | ``"error"``
            - ``raw_output``  (str)   – Raw stdout from MpCmdRun.
    """
    file_path = str(Path(file_path).resolve())

    if not os.path.isfile(file_path):
        return {
            "detected": None,
            "threat_name": "",
            "status": "error",
            "raw_output": f"File not found: {file_path}",
        }

    defender_bin = _find_defender()
    use_wine = False

    if defender_bin is None:
        # Try Wine on Linux/macOS
        if os.path.isfile(_WINE_PATH) and _DEFENDER_PATHS:
            # Use the first candidate path under Wine
            defender_bin = _DEFENDER_PATHS[0]
            use_wine = True
        else:
            return {
                "detected": None,
                "threat_name": "",
                "status": "unavailable",
                "raw_output": "Windows Defender (MpCmdRun.exe) not found.",
            }

    # Build the command
    mpcmd_args = [defender_bin, "-Scan", "-ScanType", "3", "-File", file_path]
    if use_wine:
        cmd = [_WINE_PATH] + mpcmd_args
    else:
        cmd = mpcmd_args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        raw_output = result.stdout + result.stderr
        parsed = _parse_defender_output(raw_output)
        parsed["raw_output"] = raw_output
        return parsed

    except subprocess.TimeoutExpired:
        return {
            "detected": None,
            "threat_name": "",
            "status": "error",
            "raw_output": "MpCmdRun.exe timed out after 120 seconds.",
        }
    except Exception as exc:
        return {
            "detected": None,
            "threat_name": "",
            "status": "error",
            "raw_output": str(exc),
        }
