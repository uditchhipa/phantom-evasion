#!/usr/bin/env python3
"""
Phantom Evasion - CLI Entry Point

LEGAL DISCLAIMER:
This tool is intended for authorized penetration testing and security research ONLY.
Users must have explicit written permission from the target system owner before use.
Unauthorized use is illegal and unethical. The authors assume no liability for misuse.
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich import print as rprint

from core.loader import PayloadLoader
from core.obfuscator import Obfuscator
from core.compiler import Compiler
from core.tester import Tester

console = Console()

BANNER = r"""
[bold red]
  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
[/bold red]
[bold yellow]  ███████╗██╗   ██╗ █████╗ ███████╗██╗ ██████╗ ███╗   ██╗[/bold yellow]
[bold yellow]  ██╔════╝██║   ██║██╔══██╗██╔════╝██║██╔═══██╗████╗  ██║[/bold yellow]
[bold yellow]  █████╗  ██║   ██║███████║███████╗██║██║   ██║██╔██╗ ██║[/bold yellow]
[bold yellow]  ██╔══╝  ╚██╗ ██╔╝██╔══██║╚════██║██║██║   ██║██║╚██╗██║[/bold yellow]
[bold yellow]  ███████╗ ╚████╔╝ ██║  ██║███████║██║╚██████╔╝██║ ╚████║[/bold yellow]
[bold yellow]  ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/bold yellow]
"""

DISCLAIMER = """[bold red]⚠  LEGAL DISCLAIMER ⚠[/bold red]
[yellow]This tool is for AUTHORIZED penetration testing and security research ONLY.
You MUST have explicit written permission from the target system owner.
Unauthorized use violates computer crime laws and is strictly prohibited.
The authors assume NO liability for illegal or unethical use of this tool.[/yellow]"""

TECHNIQUES_TABLE = {
    "Encryption": ["xor", "aes", "rc4", "chacha20"],
    "Obfuscation": ["string_obfuscate", "junk_code", "polymorphic", "control_flow_flatten"],
    "EDR Bypass": ["direct_syscalls", "indirect_syscalls", "unhook_ntdll", "api_hashing", "hells_gate"],
    "ETW/AMSI Bypass": ["patch_etw", "patch_amsi"],
    "Injection": ["classic", "apc", "early_bird", "callback"],
    "Sandbox Evasion": ["sleep_encrypt", "env_checks", "parent_spoof", "delayed_exec"],
    "XDR Evasion": ["process_masquerade", "network_evasion", "log_tampering"],
}


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f).get("phantom_evasion", {})
    return {}


def print_banner() -> None:
    """Print the ASCII banner and legal disclaimer."""
    console.print(BANNER)
    console.print(Panel(DISCLAIMER, border_style="red", expand=False))
    console.print()


def print_step(step: str, status: str = "✓", style: str = "green") -> None:
    """Print a progress step with a checkmark."""
    console.print(f"  [{style}]{status}[/{style}] {step}")


@click.group(invoke_without_command=True)
@click.option("--input", "-i", "input_file", type=click.Path(exists=True),
              help="Input shellcode file (.bin/.raw/.hex/.txt)")
@click.option("--output", "-o", "output_file", default="output/payload",
              help="Output file path (without extension)")
@click.option("--format", "output_format", default="exe",
              type=click.Choice(["exe", "dll", "bin"], case_sensitive=False),
              help="Output format (default: exe)")
@click.option("--edr-bypass", "edr_bypass",
              type=click.Choice(["none", "basic", "full"], case_sensitive=False),
              default="full", help="EDR bypass level (default: full)")
@click.option("--techniques", "-t", multiple=True,
              help="Extra techniques to apply (repeatable)")
@click.option("--encryption", "-e",
              type=click.Choice(["xor", "aes", "rc4", "chacha20"], case_sensitive=False),
              default="aes", help="Encryption scheme (default: aes)")
@click.option("--loader", "-l",
              type=click.Choice(["c", "rust", "go"], case_sensitive=False),
              default="c", help="Loader language (default: c)")
@click.option("--test-av", is_flag=True, default=False,
              help="Test output against Windows Defender")
@click.option("--iterations", default=10, show_default=True,
              help="Max obfuscation iterations when --test-av is used")
@click.option("--list-techniques", is_flag=True, default=False,
              help="List all available techniques and exit")
@click.pass_context
def cli(
    ctx: click.Context,
    input_file: Optional[str],
    output_file: str,
    output_format: str,
    edr_bypass: str,
    techniques: tuple,
    encryption: str,
    loader: str,
    test_av: bool,
    iterations: int,
    list_techniques: bool,
) -> None:
    """
    Phantom Evasion - Payload Obfuscation Engine

    \b
    For authorized penetration testing and security research ONLY.
    Users must have explicit written permission from the target owner.

    \b
    Example:
        python main.py -i shellcode.bin -o output/payload --encryption aes --edr-bypass full
    """
    print_banner()

    if list_techniques:
        _list_techniques()
        return

    if input_file is None:
        console.print("[yellow]No input file specified. Use --input/-i to provide a shellcode file.[/yellow]")
        console.print("Run [bold]python main.py --help[/bold] for usage information.")
        return

    cfg = load_config()

    run_pipeline(
        input_file=input_file,
        output_file=output_file,
        output_format=output_format,
        edr_bypass=edr_bypass,
        techniques=list(techniques),
        encryption=encryption,
        loader=loader,
        test_av=test_av,
        iterations=iterations,
        config=cfg,
    )


def _list_techniques() -> None:
    """Print all available techniques in a formatted table."""
    table = Table(title="Available Techniques", border_style="cyan", show_lines=True)
    table.add_column("Category", style="bold cyan", no_wrap=True)
    table.add_column("Techniques", style="white")
    table.add_column("Layer", style="yellow")

    layer_map = {
        "Encryption": "Layer 1 - Static Evasion",
        "Obfuscation": "Layer 1 - Static Evasion",
        "EDR Bypass": "Layer 2 - EDR Bypass",
        "ETW/AMSI Bypass": "Layer 3 - ETW/AMSI Bypass",
        "Injection": "Layer 4 - Behavioral Evasion",
        "Sandbox Evasion": "Layer 4 - Behavioral Evasion",
        "XDR Evasion": "Layer 4 - Behavioral Evasion",
    }

    for category, techs in TECHNIQUES_TABLE.items():
        table.add_row(category, "\n".join(techs), layer_map.get(category, ""))

    console.print(table)


def run_pipeline(
    input_file: str,
    output_file: str,
    output_format: str,
    edr_bypass: str,
    techniques: list,
    encryption: str,
    loader: str,
    test_av: bool,
    iterations: int,
    config: dict,
) -> None:
    """Execute the full obfuscation pipeline."""
    console.print(Panel("[bold cyan]Starting Phantom Evasion Pipeline[/bold cyan]", expand=False))
    console.print()

    # Build pipeline config: start with yaml defaults, then apply CLI overrides.
    # Exclude "techniques" from the yaml config (it's a dict of lists keyed by
    # category) to avoid conflicting with the CLI "techniques" tuple of names.
    pipeline_config = {k: v for k, v in config.items() if k != "techniques"}
    pipeline_config.update({
        "encryption": encryption,
        "edr_bypass": edr_bypass,
        "techniques": list(techniques),   # CLI-supplied extra technique names
        "loader": loader,
        "output_format": output_format,
    })

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    loader_obj = PayloadLoader()
    obfuscator = Obfuscator()
    compiler_obj = Compiler()
    tester = Tester()

    # Step 1: Load payload
    console.print("[bold]Phase 1:[/bold] Loading Payload")
    try:
        payload_meta = loader_obj.load(input_file)
        print_step(
            f"Loaded [cyan]{input_file}[/cyan] "
            f"([green]{payload_meta['size']}[/green] bytes, "
            f"SHA256: [dim]{payload_meta['sha256'][:16]}…[/dim])"
        )
        print_step(f"Payload type: [cyan]{payload_meta['type']}[/cyan]")
    except Exception as exc:
        console.print(f"[bold red]✗ Failed to load payload:[/bold red] {exc}")
        sys.exit(1)

    shellcode: bytes = payload_meta["shellcode"]
    console.print()

    # Step 2: Apply obfuscation layers
    console.print("[bold]Phase 2:[/bold] Applying Obfuscation Layers")
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Applying layers…", total=4)

            obfuscated = obfuscator.apply_all_layers(shellcode, pipeline_config)
            progress.advance(task, 4)

        print_step("Layer 1 – Static Evasion (encryption + code obfuscation)")
        print_step("Layer 2 – EDR Bypass (syscalls / unhooking / API hashing)")
        print_step("Layer 3 – ETW/AMSI Bypass")
        print_step("Layer 4 – Behavioral Evasion (sandbox / injection)")
        console.print(f"  [dim]Techniques applied: {obfuscated.get('description', 'N/A')}[/dim]")
    except Exception as exc:
        console.print(f"[bold red]✗ Obfuscation failed:[/bold red] {exc}")
        sys.exit(1)

    console.print()

    # Step 3: Compile
    console.print("[bold]Phase 3:[/bold] Compiling Loader")
    template_map = {
        "c": str(Path(__file__).parent / "templates" / "loader_c.c"),
        "rust": str(Path(__file__).parent / "templates" / "loader_rust.rs"),
        "go": str(Path(__file__).parent / "templates" / "loader_go.go"),
    }
    template_path = template_map[loader]
    out_path = f"{output_file}.{output_format}"

    try:
        compile_methods = {
            "c": compiler_obj.compile_c,
            "rust": compiler_obj.compile_rust,
            "go": compiler_obj.compile_go,
        }
        success = compile_methods[loader](template_path, out_path, obfuscated)
        if success:
            print_step(f"Compiled [cyan]{loader.upper()}[/cyan] loader → [green]{out_path}[/green]")
        else:
            print_step("Compiler not found; writing C source to disk instead", "⚠", "yellow")
            src_path = f"{output_file}.c"
            _write_source(template_path, src_path, obfuscated)
            print_step(f"Source written to [cyan]{src_path}[/cyan]", "✓", "yellow")
    except Exception as exc:
        console.print(f"[bold red]✗ Compilation failed:[/bold red] {exc}")
        sys.exit(1)

    console.print()

    # Step 4: AV testing (optional)
    if test_av:
        console.print("[bold]Phase 4:[/bold] AV Detection Testing")
        try:
            if test_av and Path(out_path).exists():
                result = tester.iterative_test(shellcode, pipeline_config, iterations)
                if result.get("bypassed"):
                    print_step(f"Payload bypassed AV after [green]{result.get('iterations')}[/green] iteration(s)")
                else:
                    print_step("Payload detected after max iterations", "✗", "red")
            else:
                print_step("Skipping AV test – compiled binary not found", "⚠", "yellow")
        except Exception as exc:
            console.print(f"[bold yellow]⚠ AV testing skipped:[/bold yellow] {exc}")

        console.print()

    console.print(Panel(
        f"[bold green]✓ Pipeline complete![/bold green]\n"
        f"Output: [cyan]{out_path}[/cyan]",
        border_style="green",
        expand=False,
    ))


def _write_source(template_path: str, out_path: str, obfuscated: dict) -> None:
    """Write the filled C source template to disk (fallback when compiler absent)."""
    try:
        with open(template_path) as f:
            source = f.read()
    except FileNotFoundError:
        source = "/* Template not found */\n"

    replacements = {
        "/* PLACEHOLDER: decryption_key */": obfuscated.get("encryption_code", ""),
        "/* PLACEHOLDER: encrypted_shellcode */": "",
        "/* PLACEHOLDER: decryption_routine */": obfuscated.get("encryption_code", ""),
        "/* PLACEHOLDER: evasion_techniques */": "\n".join([
            obfuscated.get("edr_code", ""),
            obfuscated.get("etw_code", ""),
            obfuscated.get("behavioral_code", ""),
        ]),
        "/* PLACEHOLDER: injection_method */": obfuscated.get("injection_code", ""),
    }
    for placeholder, replacement in replacements.items():
        source = source.replace(placeholder, replacement)

    with open(out_path, "w") as f:
        f.write(source)


if __name__ == "__main__":
    cli()
