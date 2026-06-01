# Highlight: Recruit Plus — chaining vulnerabilities

**Category:** Web (JWT + file upload + path traversal)
**Difficulty:** Hard
**Time to solve:** ~30 minutes
**Why it makes the post:** Cleanest example of chaining multiple bugs to escalate. A single bug in this app would have been a footnote. Three bugs in sequence = full admin compromise.

## What we were given

A recruitment portal — log in, see a dashboard, upload your résumé. The scenario brief: "find a way to login as admin." Source code provided.

## The three bugs

**Bug #1 — JWT verification with a misspelled option.**

```javascript
return jwt.verify(token, pubkey, { algorithm: 'RS256' });
```

The `jsonwebtoken` library's option is `algorithms` *plural* — an array. Passing `algorithm` *singular* doesn't error; it gets silently ignored, and the library falls back to inferring the allowed algorithm from the key shape. That means the library will accept *any* algorithm the attacker specifies in the JWT header, not just RS256.

Common attack: switch from RS256 to HS256 and use the (public) RSA key as the HMAC secret. The library, not seeing an algorithm restriction, validates the HS256 signature using the "key" — and the validation succeeds.

In modern `jsonwebtoken` this attack is partially blocked by a runtime check that refuses PEM-shaped strings as HMAC secrets. That check defeated my first attempt.

**Bug #2 — `kid` header used as a file path with no sanitization.**

```javascript
keyId = jwt.decode(token, { complete: true }).header.kid;
keyFile = path.join(__dirname, '/../private', keyId);
return fs.readFileSync(keyFile, 'utf8');
```

`path.join` doesn't reject `../` traversal — it just normalizes the path. So a JWT with `kid: "../../../../etc/passwd"` would read `/etc/passwd` and try to use its contents as the verification key.

**Bug #3 — File upload that lets you control file contents on disk.**

The résumé-upload endpoint accepts `.doc` and `.docx` files. It saves them at `uploads/<md5>.doc`. The MD5 means the filename is predictable (we know what we uploaded, so we know the hash).

## The chain

These bugs compose:

1. Register a normal user, log in to get a valid session (needed to pass the auth check on `/api/upload`)
2. Upload a tiny `.doc` file with known content — say, the 6-byte string `simona`
3. The server saves it at `uploads/<known-md5>.doc`
4. Forge a JWT:
   - **Algorithm:** HS256
   - **Kid:** `"../uploads/<md5>.doc"` (path-traverses out of `/private/` into `/uploads/`)
   - **Payload:** `{"username": "admin"}`
   - **Signature:** `HMAC-SHA256(signing_input, "simona")` — the same string we uploaded
5. Submit the forged token. The server reads our uploaded file as the "verification key," computes HMAC-SHA256 using its contents, matches our signature, accepts the token as `username: admin`.
6. `/dashboard` checks `if (user.username == "admin") flag = fs.readFileSync('/flag', 'utf8')`. Flag returned.

The flag was on-the-nose: `HTB{1_h4v3_r5a_Tru5t_i55u3s}`.

## What the chain teaches

No single bug in isolation would have been usable:

- The misspelled `algorithm` option alone is mostly mitigated by the runtime PEM check
- The `kid` traversal alone is useless without something to point it at
- The file upload alone is harmless — `.doc` files in `uploads/` aren't executable, they're just static

But composed: misspelled option means HS256 with arbitrary-key-material is accepted → kid traversal lets us point at any file as the key material → file upload lets us *control* the file contents.

This is what real-world exploit chains look like. CVEs that get chained — each "low severity" on its own, "critical" when composed. SAST tools that score bugs individually miss this composition. AI pattern-matching across multiple files at once does not.

## How Simona spotted it

Triage order:
1. Read `JWTHelper.js` first (file named "JWTHelper" is always where JWT bugs hide). Spotted misspelled `algorithm` in <30 seconds.
2. Read `AuthMiddleware.js` — confirmed the kid is taken directly from the JWT and passed to `getKey()`.
3. Re-read `JWTHelper.getKey()`. Spotted the `path.join(__dirname, '/../private', keyId)`. Immediately flagged the traversal.
4. Now needed to find something to traverse *to*. Read `routes/index.js`. Spotted `/api/upload` with predictable filenames in `/uploads/`. Chain complete.

Total time from "what is this app" to "I know how to compromise it": about 5 minutes of reading. The remaining 25 minutes was implementing the exploit script and debugging one network sequencing bug (when to send the upload vs the forged JWT).

## Suggested LinkedIn quote

> "One web challenge gave us three bugs in the same code base. A misspelled option in a JWT verify call. A path traversal in the 'kid' header that fed into `fs.readFileSync`. A file upload endpoint. Each was annoying-but-mostly-mitigated on its own. Composed, they were a full admin takeover in five minutes of analysis and 25 minutes of plumbing. This is what real exploit chains look like — and what makes them hard for traditional security scanners. SAST tools score bugs individually. AI reads three files at once and asks 'wait, what happens if I compose these?' That's the actual skill."
