#!/usr/bin/env python3
"""Disassemble the final-stage PE and hunt for the flag-construction logic."""
import pefile, capstone, re

pe = pefile.PE("/tmp/td_finalstage.bin")
print("Image base:", hex(pe.OPTIONAL_HEADER.ImageBase))
print("Entry point:", hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
print("Sections:")
for s in pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin-1')
    print(f"  {name:10s} vaddr={hex(s.VirtualAddress)} vsize={hex(s.Misc_VirtualSize)} rawoff={hex(s.PointerToRawData)} rawsize={hex(s.SizeOfRawData)}")

# Find imports
print("\nImports:")
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    print(f"  {entry.dll.decode('latin-1')}")
    for imp in entry.imports:
        if imp.name:
            print(f"    {hex(imp.address)}  {imp.name.decode('latin-1')}")

# Disassemble .text section
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
text = next(s for s in pe.sections if s.Name.startswith(b'.text'))
code = text.get_data()
base = pe.OPTIONAL_HEADER.ImageBase + text.VirtualAddress

# Look for sequences that build stack strings — mov dword ptr [ebp+xx], imm
# Stack strings often look like: mov [ebp-N], imm32  with imm32 being 4 ASCII chars
print("\n--- candidate stack-string mov instructions (4 printable ASCII bytes as imm32) ---")
hits = []
for insn in md.disasm(code, base):
    s = insn.op_str
    # mov DWORD PTR [...], 0xNNNNNNNN
    m = re.match(r'(dword|word|byte) ptr \[(.+)\], (0x[0-9a-f]+)', s)
    if m:
        try:
            imm = int(m.group(3), 16)
        except: continue
        if m.group(1) == 'dword':
            bs = imm.to_bytes(4, 'little')
        elif m.group(1) == 'word':
            bs = imm.to_bytes(2, 'little')
        else:
            bs = imm.to_bytes(1, 'little')
        # Check if all bytes printable
        if all(0x20 <= b <= 0x7e or b == 0 for b in bs) and any(0x20 <= b <= 0x7e for b in bs):
            hits.append((insn.address, m.group(2), bs))

# Group consecutive [ebp-N] writes
prev_addr = None
prev_disp = None
combined = []
buf = []
for addr, disp, bs in hits:
    if not buf:
        buf = [(addr, disp, bs)]
    elif addr - buf[-1][0] < 40:  # close together
        buf.append((addr, disp, bs))
    else:
        if len(buf) >= 2:
            combined.append(buf)
        buf = [(addr, disp, bs)]
if len(buf) >= 2:
    combined.append(buf)

for group in combined:
    addrs = [g[0] for g in group]
    print(f"\n  cluster at {hex(group[0][0])} (n={len(group)}):")
    for addr, disp, bs in group:
        try:
            ascii_part = bs.decode('latin-1').replace('\x00','.')
        except:
            ascii_part = '?'
        print(f"    {hex(addr):10s}  [{disp}] = {bs.hex()}  '{ascii_part}'")
    # Reconstruct as one byte stream sorted by disp offset
    parts = []
    for addr, disp, bs in group:
        # try parse displacement
        m = re.search(r'ebp\s*([+-])\s*(0x[0-9a-f]+|\d+)', disp)
        if m:
            sign = 1 if m.group(1) == '+' else -1
            try:
                v = int(m.group(2), 0)
                parts.append((sign*v, bs))
            except: pass
    parts.sort()
    raw = b''.join(b for _, b in parts)
    print(f"    -> reconstructed: {raw!r}")
    # try utf-16-le decode
    try:
        u = raw.decode('utf-16-le', errors='ignore')
        if any(c.isprintable() for c in u):
            print(f"    -> as UTF-16-LE: {u!r}")
    except: pass
