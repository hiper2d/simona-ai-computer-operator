# Domain breadth — what one participant had to know

The argument for the LinkedIn piece: solo humans don't carry this surface in working memory. CTF teams are usually 3–5 people specifically because the categories require different specializations. AI shifts the math.

Below is the actual knowledge inventory that came up across the 19 challenges.

## Windows internals

- **Registry format (regf):** parsing NTUSER.DAT and SOFTWARE hives manually. Distinguishing HKCU vs HKLM persistence. Reading the value/subkey structure. Understanding which keys are common attacker targets (`\Run`, `\RunOnce`, Winlogon `Userinit`/`Shell`, Image File Execution Options `Debugger`, Active Setup `StubPath`, Credential Providers, COM CLSID `InprocServer32`).
- **PowerShell internals:** the AMSI bypass pattern (patching `amsiInitFailed`), the ETW disable (patching `m_enabled` on `PSEtwLogProvider`), `-EncodedCommand` base64+UTF-16-LE, the `$ShellId[1]+$ShellId[13]+'x'` IEX trick.
- **.NET framework:** Reflective `Assembly.Load(byte[])`, BinaryFormatter deserialization gadgets ("GadgetToJScript"), `RijndaelManaged` with non-standard block sizes, `Rfc2898DeriveBytes` (PBKDF2), the `#US` user-strings stream layout in metadata.
- **Process hollowing:** the canonical sequence — `CreateProcess(suspended)`, `NtUnmapViewOfSection`, `VirtualAllocEx`, `NtWriteVirtualMemory` (header + sections), `NtGetContextThread`, modify entry point, `NtSetContextThread`, `NtResumeThread`.
- **Credential Providers:** rogue DLLs registered via CLSID + `Authentication\Credential Providers\{guid}` — runs on every logon, can capture passwords.
- **Windows shortcut (LNK) format:** target path, command-line arguments, working directory, icon, NetBIOS hostname and volume serial number in the extra-data blocks.
- **PE format:** MZ header, e_lfanew → PE header, sections, imports, .rdata vs .data, GOT/IAT.

## Linux internals

- **ELF format:** entry point, segments, sections, dynamic linking
- **glibc:** `__libc_csu_init` universal gadget pair, the differences between glibc <2.34 and >=2.34 startup, `__libc_start_main` vs `__libc_start_call_main`
- **ASLR / NX / PIE / RELRO:** what each mitigation does, what combinations leave open
- **Stack frame layout:** how locals, saved rbp, return address sit on the stack
- **x86-64 SysV calling convention:** rdi, rsi, rdx, rcx, r8, r9 for first 6 args; movaps alignment requirements at `system()`
- **ROP:** finding gadgets (pop sequences ending in `ret`), chain construction, dealing with stack alignment

## Web stack

- **JWT internals:** header/payload/signature structure, HS256 vs RS256, the `alg: none` attack, the HS-with-public-key confusion attack, the `kid` (key ID) header and how libraries use it for key lookup
- **SQL injection variants:** UNION-based, error-based, boolean blind, time-based, second-order, ORDER BY (where you can't use `?` placeholders), how to steer an injection at a specific row rather than just bypass
- **XSS variants:** reflected, stored, DOM-based, blind (where the payload fires in an admin's browser, not the attacker's)
- **Server-side template engines:** Nunjucks (Node), Jinja2 (Python), the `autoescape: false` footgun
- **CORS / SOP / origin policy:** how a stored XSS in one path can exfil data from another path on the same origin
- **HTTP itself:** form encoding, multipart upload, cookie handling, redirects

## Cryptography

- **RSA math:** `n = p × q`, `phi(n) = (p-1)(q-1)`, `d = e^-1 mod phi(n)`, `c = m^e mod n`, `m = c^d mod n`
- **RSA failure modes:** prime power moduli (`n = p^r`), Wiener attack (small d), Boneh-Durfee, Hastad broadcast, Fermat factorization, ROCA, padding oracles
- **PBKDF2 (Rfc2898DeriveBytes):** password + salt → derived key via iterated HMAC-SHA1
- **AES vs Rijndael:** AES is fixed 128-bit block; Rijndael allows 192 and 256-bit blocks too (the Time Dilation malware used Rijndael-256/256)
- **XOR ciphers:** properties (commutative, associative, self-inverse, identity), why N layers collapse to 1, how known-plaintext breaks repeating-key XOR

## Reverse engineering

- **x86-64 assembly:** reading objdump output fluently, recognizing function prologues/epilogues, identifying calling conventions
- **.NET IL:** opcodes (ldarg, ldloc, ldstr, call, callvirt, newobj, ldsfld), tiny vs fat method headers, the #US heap layout
- **Static analysis tools:** objdump, nm, readelf, strings, file (libmagic), pyelftools, dnfile, pylnk3, monodis
- **Dynamic analysis (we didn't use much, but it's part of the surface):** gdb, pwndbg, GEF, strace, ltrace

## Network forensics

- **pcap format:** libpcap binary structure
- **TCP stream reassembly:** ordering by sequence number, dedup, handling retransmissions
- **HTTP over TCP:** request/response framing, content-length, chunked encoding
- **Tooling:** scapy, tshark, Wireshark

## File format zoology

- regf (Windows registry hive)
- LNK (Windows shortcut)
- ELF (Linux binary)
- PE/PE32+ (Windows binary, both native and .NET CIL)
- DOS MZ stub
- PEM (RSA keys)
- base64 (multiple variants: standard, URL-safe, with/without padding)
- UTF-16-LE (Windows native, length-prefixed in .NET #US heap)
- pcap (libpcap binary)
- JWT (header.payload.signature, base64url)

## Languages

The challenges required reading code in:

- C (most pwn binaries, source provided)
- Python (most web challenges, Flask)
- JavaScript / Node.js (Express web challenges)
- PowerShell (forensics payloads)
- VBScript (forensics — the BinaryFormatter dropper)
- C# / .NET IL (the Time Dilation reflective payload)
- x86-64 assembly (pwn challenges, reading disassembly)
- SQL (injection challenges)
- HTML / CSS (web challenges)
- YAML (config files in some challenges)
- Bash / shell (Docker setups, build scripts)

## Tooling

What I actually invoked during the session:

- `unzip`, `file`, `strings`, `nm`, `objdump`, `xxd`
- `curl`, `socket` (raw Python), `scapy`
- `python-registry`, `dnfile`, `pylnk3`, `pyelftools`
- `pycryptodome`, `gmpy2`
- `mono`, `mcs`, `monodis` (installed mid-session)
- `capstone` (disassembly engine)
- `webhook.site` (for blind XSS exfil)

That's about 25 distinct tools, several of which I installed on the fly when I realized I needed them. A solo human under time pressure doesn't have time to install/learn new tools mid-CTF. That's a real advantage of AI pairing — the tool inventory is effectively infinite.

## The thesis

No human carries all of this in working memory. Top CTF players are exceptional generalists, but they still specialize. A solo human in a 6-hour event makes hard prioritization calls (skip pwn, skip crypto, focus on web) precisely because they can't span the breadth.

AI removes the breadth constraint. It doesn't make you better at any one category. It removes the requirement to be deep in all of them. The leverage isn't *capability* — it's *coverage*.

That's the line worth landing in the LinkedIn piece, because it's the version that's defensible to skeptics. A senior pentester can outperform AI in their specialty. They can't outperform AI across 6 specialties simultaneously, because no one can.
