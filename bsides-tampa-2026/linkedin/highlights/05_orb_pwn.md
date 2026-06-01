# Highlight: Orb — where AI was slow (the humility moment)

**Category:** Pwn (binary exploitation)
**Difficulty:** Medium textbook; the *debugging* was the slow part
**Time to solve:** ~40 minutes (designed in 5, debugged in 35)
**Why it makes the post:** Honesty signal. The post needs at least one challenge where AI struggled — otherwise it reads as marketing. This is the cleanest example of where pattern recognition wins but precise execution stumbles.

## What we were given

A Linux ELF binary called "Orb" — themed as a magic artifact you need to escape. Plus a copy of the libc the binary linked against (so we'd know exact offsets to symbols like `system` and `/bin/sh`).

## The vulnerability

Trivial to spot. Main does:

```
read(0, buf=rbp-0x20, 0x100)
```

A 32-byte stack buffer being filled with up to 256 bytes. Past 32 buf + 8 saved rbp = **40 bytes of padding**, then we control the return address.

## The plan (5 minutes to design)

Standard two-stage ret2libc:

**Stage 1 — leak libc.** Need to find out where libc loaded in memory this run (ASLR randomizes it). Standard trick: call `write(1, write@got, 8)` which prints the 8 bytes of `write@got` — that GOT entry holds the resolved libc address of `write` after the binary's first call to it. From that leaked address + the known offset of `write` inside libc, compute the libc base.

**Stage 2 — system("/bin/sh").** With libc base known: `system_addr = libc_base + 0x4f420`. `binsh_addr = libc_base + 0x1b3d88`. Standard ROP: `ret-for-alignment + pop rdi + binsh_addr + system_addr` and a shell pops.

The chain itself is generic textbook. I've "seen" hundreds of these in training data.

## Where it got slow (35 minutes of debugging)

The exploit failed three times. Each failure was a **byte-counting bug at the network boundary** — not a chain-design bug.

**Failure 1.** The leaked 8 bytes I parsed weren't a libc address. They decoded to ASCII text starting with `\nThi`. My buffer-read had captured the trailing message from the previous main iteration ("This spell does not seem to work..") instead of the actual leak bytes.

**Failure 2.** Fixed the marker — `recvuntil("This spell does not seem to work..\n\n")` to drain that message first. Now the leak parsed as a "libc address" but the math was off by one byte. After computing `libc_base = leak - 0x1100f0`, the result wasn't page-aligned (libc bases are always 4KB-aligned). Wrong leak position.

**Failure 3.** Investigated the trailing message bytes more carefully. The string was actually 38 bytes ending in `\n\n\x00\x00` (with TWO trailing nulls). My marker only consumed `\n\n`, so the next 2 bytes I read were the trailing nulls, not the leak bytes. Shifted everything by 2.

Each "failure" was 5–10 minutes of running the exploit, capturing the failure mode, instrumenting the receive loop, dumping hex, re-reading the binary's data section to find the actual trailing byte count, fixing the marker. Three iterations until the leak parser was right.

## What a senior human would have done differently

Two things:

1. **Use `pwntools`.** It's the standard pwn library, exists *because* humans got tired of byte-counting bugs. `pwntools` gives you `p.recvline()`, `p.recvuntil()`, `p.interactive()` — abstractions that handle terminal sequencing correctly. Simona used raw Python sockets because "use the standard library" is the default heuristic. For pwn, that's the *wrong* default.

2. **Instrument first, parse later.** A senior would have done one run that just dumped 16 bytes of hex around the suspected leak position, eyeballed the structure visually, and *then* written the parser. I built the parser too early, then had to rewrite it three times when its assumptions broke.

The chain design wasn't the issue. The I/O layer was. And that's a real class of weakness AI has compared to specialists: AI doesn't have the muscle memory for "always instrument before you parse."

## What a human PAIRED with AI does

This is the actual workflow:
- AI designs the chain (5 minutes — fast)
- AI writes the first attempt (1 minute — fast)
- Human sees it fail and says "OK, stop, dump the wire bytes first instead of guessing the structure" (one comment)
- AI takes the suggestion, dumps the bytes, fixes the parser (5 minutes — fast)
- Done in 10 minutes total instead of 40

I didn't have Alex paired *on* this challenge (he was busy with other event activities). Solo Simona burned the time. Solo Alex, with no AI, would have spent hours getting the chain design right but probably hit the byte-count bugs faster because he has pwntools fluency.

The pair: ~10 minutes total. Either alone: 40+ minutes. The leverage isn't either party; it's the loop between them.

## Suggested LinkedIn quote

> "I want to be honest about where AI was slow. One pwn challenge took 40 minutes — and the chain design was 5 of those. The other 35 was Simona iterating on a network-buffer parser that kept being off-by-one or off-by-two because she didn't think to dump raw bytes before writing the parser. A senior pentester would have hit this in 10 minutes, because they have muscle memory for 'always instrument the wire first.' AI doesn't have that muscle memory — it has pattern recognition, which is faster for design and slower for execution. The right pairing is: AI for design, human for sanity-checking the I/O. Either alone is slower than both together."
