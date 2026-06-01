#!/usr/bin/env python3
"""Hunt for persistence in an NTUSER.DAT hive."""
from Registry import Registry

HIVE = "/tmp/persist/NTUSER.DAT"
reg = Registry.Registry(HIVE)

# Classic per-user persistence keys
PERSISTENCE_KEYS = [
    r"Software\Microsoft\Windows\CurrentVersion\Run",
    r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
    r"Software\Microsoft\Windows\CurrentVersion\RunServices",
    r"Software\Microsoft\Windows\CurrentVersion\RunServicesOnce",
    r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon",
    r"Software\Microsoft\Windows NT\CurrentVersion\Windows",
    r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Run",
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
    r"Environment",
    r"Software\Classes\exefile\shell\open\command",
    r"Software\Classes\mscfile\shell\open\command",
    r"Software\Classes\ms-settings\shell\open\command",
]

print("="*70)
print("PERSISTENCE KEY SWEEP")
print("="*70)
for path in PERSISTENCE_KEYS:
    try:
        k = reg.open(path)
    except Registry.RegistryKeyNotFoundException:
        continue
    vals = list(k.values())
    subs = list(k.subkeys())
    if not vals and not subs:
        continue
    print(f"\n[KEY] {path}    (modified: {k.timestamp()})")
    for v in vals:
        val = v.value()
        if isinstance(val, bytes):
            val = val.hex()[:200] + "..." if len(val) > 100 else val.hex()
        sval = str(val)
        if len(sval) > 400:
            sval = sval[:400] + " ..."
        print(f"    {v.name()} = {sval}")
    for s in subs:
        print(f"    [subkey] {s.name()}")

# Now walk EVERYTHING looking for HTB{ and suspicious commands
print("\n" + "="*70)
print("FULL HIVE GREP — HTB{...}, base64-ish, scripting engines")
print("="*70)

import re
HTB_RE = re.compile(r"HTB\{[^}]+\}")
SUSP_RE = re.compile(r"(powershell|cmd\.exe|wscript|cscript|mshta|rundll32|regsvr32|certutil|bitsadmin|FromBase64|-enc\s|-EncodedCommand)", re.I)

def walk(key, depth=0):
    for v in key.values():
        try:
            val = v.value()
        except Exception:
            continue
        if isinstance(val, bytes):
            try:
                val = val.decode('utf-16-le', errors='ignore')
            except Exception:
                continue
        sval = str(val)
        if HTB_RE.search(sval) or SUSP_RE.search(sval):
            print(f"[HIT] {key.path()}  ::  {v.name()} = {sval[:500]}")
    for s in key.subkeys():
        try:
            walk(s, depth+1)
        except Exception as e:
            pass

walk(reg.root())
