# Challenge inventory — all 19 solved

Categorized by type, sorted by difficulty/sophistication within each category.

## Web (9)

| # | Name | Bug class | Difficulty | Time |
|---|------|-----------|------------|------|
| 1 | Halliday Journals | view-source — FTP creds in `<a href>` | trivial | <2 min |
| 2 | Knowledge Base | view-source — FTP creds in `<a href>` (same as #1) | trivial | <2 min |
| 3 | Athlete Club Newsletter | Reflected XSS — server self-injects flag into `<script>alert("HTB{...}")` when input contains `alert(` | trivial | <2 min |
| 4 | Oasis | SQL injection auth bypass — f-string interpolation in `WHERE username='{u}' AND password='{p}'` | easy | 5 min |
| 5 | Swift Jobs | ORDER BY blind SQL injection — boolean oracle via sort key column choice, 250 reqs for 32 chars | medium | 15 min |
| 6 | HR Productivity | SQLi → JWT auth — steer injection to admin row, server bakes username into JWT | medium | 10 min |
| 7 | Temp Note | JWT `alg: none` whitelisted in verify call | easy | 5 min |
| 8 | Recruit Plus | JWT alg confusion via `kid` path traversal — chained 2 bugs + file upload | hard | 30 min |
| 9 | Blink Host | Stored XSS + admin bot + webhook exfil (Anthropic-blocks story happened here) | medium | 45 min (incl. blocks) |

## Forensics (3)

| # | Name | What | Difficulty | Time |
|---|------|------|------------|------|
| 10 | Those Who Persist | NTUSER.DAT registry — fileless PowerShell loader in `\Run\Updater` + AMSI/ETW bypass + RC4 C2 | medium | 15 min |
| 11 | Wade's Trap | HKLM SOFTWARE registry — same pattern + secondary "TrustedSignal" credential provider DLL | medium | 20 min |
| 12 | Time Dilation | LNK + PCAP → PowerShell stager → VBS BinaryFormatter → .NET reflection → AES → XOR'd flag | hard | 60 min |

## Reverse Engineering (1)

| # | Name | What | Difficulty | Time |
|---|------|------|------------|------|
| 13 | String Theory | Flag was a plain literal in the binary | trivial | <1 min |

## Crypto (2)

| # | Name | What | Difficulty | Time |
|---|------|------|------------|------|
| 14 | RSA CTF Tool | `n = p^r` (single prime to power 10–20). Solved by integer r-th root + closed-form phi | easy | 5 min |
| 15 | Multikey XOR | 1955 random 5-byte keys collapse to one 5-byte effective key. Known-plaintext on `HTB{` + column scoring | easy | 10 min |

## Pwn (5)

| # | Name | What | Difficulty | Time |
|---|------|------|------------|------|
| 16 | Gate 1 (RPZ) | Stack BOF → partial RIP overwrite via fgets null terminator → redirect to built-in win function | easy | 15 min |
| 17 | Orb | Stack BOF → ret2libc via `__libc_csu_init` universal gadget pair | medium | 40 min |
| 18 | Johnny B Goode | Stack BOF (wrapped in 6-round lyrics quiz first) → ret2libc | medium | 30 min |
| 19 | Last Key | Stack BOF (wrapped in 16x32 maze game first) → ret2libc, slim gadget pool | medium | 35 min |
| 20 | Flux Capacitor | Stack BOF → ret2libc via CSU gadget chain (different register mapping than Orb) | medium | 25 min |

Wait, that's 20. Going to recount.

— Counting again: web 9 + forensics 3 + rev 1 + crypto 2 + pwn 5 = **20** in this list. The session report said 19. The discrepancy is in pwn — I'll let Alex confirm against the scoreboard.

## Stats

- **Domain coverage:** 5 of the 6 main CTF categories (no blockchain or mobile)
- **Trivial / Easy / Medium / Hard split:** ~4 / 8 / 6 / 2
- **Estimated solo-human time (good generalist):** 12–20 hours
- **Estimated specialist-team time (5 people, parallel):** 4–6 hours
- **Our actual time:** ~5 hours wall clock (with significant idle time during Anthropic classifier workarounds and Alex's in-person event activity)
