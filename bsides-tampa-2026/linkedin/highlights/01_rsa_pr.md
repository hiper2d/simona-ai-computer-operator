# Highlight: "RSA" that wasn't RSA

**Category:** Crypto
**Difficulty:** Easy (with the right pattern recognition); ~impossible if you don't see it
**Time to solve:** 5 minutes
**Why it makes the post:** Most accessible challenge to non-specialists. The math is one paragraph; the punchline lands instantly.

## What we were given

Three files:
- `key.pem` — looked like a standard RSA public key
- `flag.enc` — the encrypted flag
- `source.py` — the encryption script the organizers used

The `key.pem` reported a 9711-bit modulus. Standard production RSA is 2048 or 4096 bits. **9711 bits is almost 5× larger than what banks use.** The naive read is "this must be uncrackable."

## The bug

The `source.py` had this:

```python
p = getPrime(512)            # ONE 512-bit prime
r = randint(10, 20)
n = 1
for _ in range(r):
    n *= p                   # multiply n by p, r times
self.n = n                   # n = p^r, NOT p × q
```

Standard RSA: `n = p × q`, two different large primes. Security rests on the assumption that factoring `n` back into its primes is computationally infeasible (the General Number Field Sieve takes longer than the age of the universe for 2048-bit `n`).

The buggy code: `n = p^r` — one prime raised to a small power. The 9711 bits come from `512 × 19` (in this challenge's case). It LOOKS bigger; it's actually structurally weaker.

## Why it's trivial

For `n = p^r`:
- **Factoring is one line.** Take the integer r-th root for r = 2, 3, 4, ... until one returns an exact integer. That's `p`. Cost: ~25 fast computations.
- **Phi has a closed form.** `phi(p^r) = p^(r-1) × (p-1)`. No factoring search needed.
- **Decryption is mechanical.** `d = e^-1 mod phi(n)`, `m = c^d mod n`.

The full attack:

```python
import gmpy2
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes

key = RSA.import_key(open("key.pem").read())
n, e = key.n, key.e

for r in range(2, 30):
    root, exact = gmpy2.iroot(n, r)
    if exact:
        p = int(root)
        phi = p**(r-1) * (p-1)
        d = pow(e, -1, phi)
        c = bytes_to_long(open("flag.enc", "rb").read())
        m = pow(c, d, n)
        print(long_to_bytes(m))
        break
```

Five lines of math break a "9711-bit key." Flag back in seconds.

## What this means

The challenge name was a wink: `RsaCtfTool` is a well-known toolkit that automates exactly this kind of attack across 20+ known RSA failure modes. The pattern (large modulus that looks safer than it is) is a real misconception even in production systems. The lesson isn't "AI can break RSA." It's "size doesn't equal security; structure does."

## The recognition moment

Simona's pattern-match: *single prime variable + multiply-loop with same variable = prime power*. That's a one-line review-flag for anyone who's seen this category before. Total time from reading `source.py` to recognizing the bug: under 30 seconds.

A human without that pattern in their head might spend hours assuming "the 9711-bit key must be safe; what's the trick?" — looking for a math weakness in the wrong place.

## Suggested LinkedIn quote

> "An 'RSA' challenge handed me a 9711-bit modulus — nearly 5× the size of what banks use. Most people see that number and assume 'unbreakable.' Simona saw it and broke it in five lines of Python, because the modulus wasn't `p × q`. It was `p^19`. The size was a feint. The whole point of cryptography is structure, not bit count."
