#!/usr/bin/env python3
"""Hunt persistence in HKLM SOFTWARE hive."""
from Registry import Registry
import re

HIVE = "/tmp/wade/SOFTWARE"
reg = Registry.Registry(HIVE)

# Classic HKLM persistence keys
KEYS = [
    r"Microsoft\Windows\CurrentVersion\Run",
    r"Microsoft\Windows\CurrentVersion\RunOnce",
    r"Microsoft\Windows\CurrentVersion\RunServices",
    r"Microsoft\Windows\CurrentVersion\RunServicesOnce",
    r"Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
    r"Microsoft\Windows\CurrentVersion\Explorer\Run",
    r"Microsoft\Windows\CurrentVersion\Explorer\ShellExecuteHooks",
    r"Microsoft\Windows NT\CurrentVersion\Winlogon",
    r"Microsoft\Windows NT\CurrentVersion\Windows",
    r"Microsoft\Windows NT\CurrentVersion\Image File Execution Options",
    r"Microsoft\Windows NT\CurrentVersion\Drivers32",
    r"Microsoft\Windows NT\CurrentVersion\AeDebug",
    r"Microsoft\Active Setup\Installed Components",
    r"Microsoft\Windows\CurrentVersion\Authentication\Credential Providers",
    r"Microsoft\Windows NT\CurrentVersion\Svchost",
    r"WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
    r"WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce",
    r"WOW6432Node\Microsoft\Windows NT\CurrentVersion\Winlogon",
]

def dump_val(v):
    try:
        val = v.value()
    except Exception:
        return "<read error>"
    if isinstance(val, bytes):
        if len(val) > 200:
            return val.hex()[:400] + "..."
        return val.hex()
    s = str(val)
    return s if len(s) < 600 else s[:600] + " ..."

print("="*70)
print("HKLM SOFTWARE — PERSISTENCE KEY SWEEP")
print("="*70)
for path in KEYS:
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
        print(f"    {v.name()} = {dump_val(v)}")
    for s in subs:
        print(f"    [subkey] {s.name()}    (modified: {s.timestamp()})")

# IFEO sub-keys often hold the actual debugger redirects
print("\n" + "="*70)
print("IFEO SUBKEYS WITH 'Debugger' VALUE")
print("="*70)
try:
    ifeo = reg.open(r"Microsoft\Windows NT\CurrentVersion\Image File Execution Options")
    for s in ifeo.subkeys():
        try:
            d = s.value("Debugger")
            print(f"  {s.name()} -> Debugger = {d.value()}")
        except Registry.RegistryValueNotFoundException:
            pass
except Registry.RegistryKeyNotFoundException:
    pass

# Active Setup StubPath
print("\n" + "="*70)
print("ACTIVE SETUP - StubPath values")
print("="*70)
try:
    asetup = reg.open(r"Microsoft\Active Setup\Installed Components")
    for s in asetup.subkeys():
        try:
            stub = s.value("StubPath").value()
            try:
                comp = s.value("ComponentID").value()
            except Exception:
                comp = "?"
            print(f"  {s.name()}  ComponentID={comp}")
            print(f"     StubPath = {stub}")
        except Registry.RegistryValueNotFoundException:
            pass
except Registry.RegistryKeyNotFoundException:
    pass

# Winlogon Notify and Userinit/Shell explicit
print("\n" + "="*70)
print("WINLOGON DEEP — Userinit, Shell, Notify subkeys")
print("="*70)
for wpath in [r"Microsoft\Windows NT\CurrentVersion\Winlogon",
              r"WOW6432Node\Microsoft\Windows NT\CurrentVersion\Winlogon"]:
    try:
        k = reg.open(wpath)
    except Registry.RegistryKeyNotFoundException:
        continue
    for vname in ("Userinit", "Shell", "Taskman", "AppSetup", "GinaDLL", "VmApplet", "System"):
        try:
            v = k.value(vname)
            print(f"  [{wpath}] {vname} = {v.value()}")
        except Registry.RegistryValueNotFoundException:
            pass
    # Notify subkey persistence
    try:
        notify = k.subkey("Notify")
        for s in notify.subkeys():
            try:
                dll = s.value("DllName").value()
            except Exception:
                dll = "?"
            print(f"  [Notify] {s.name()} DllName={dll}")
    except Registry.RegistryKeyNotFoundException:
        pass

# COM hijack hunt: Classes\CLSID\{...}\InprocServer32 with suspicious paths
print("\n" + "="*70)
print("FULL HIVE GREP — HTB{...}, scripting engines, base64-ish patterns")
print("="*70)
HTB_RE = re.compile(r"HTB\{[^}]+\}")
SUSP_RE = re.compile(r"(powershell|cmd\.exe|wscript|cscript|mshta|rundll32|regsvr32|certutil|bitsadmin|FromBase64|-enc|-EncodedCommand|http://|https://[^/]+\.\w+|AppData\\Roaming|AppData\\Local\\Temp)", re.I)

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
        if HTB_RE.search(sval):
            print(f"[FLAG?] {key.path()}  ::  {v.name()} = {sval[:600]}")
        elif SUSP_RE.search(sval):
            # filter out the obvious vendor noise
            if any(x in sval for x in ("Microsoft Corporation", "Mozilla/", "Internet Explorer")):
                continue
            print(f"[SUSP] {key.path()}  ::  {v.name()} = {sval[:600]}")
    for s in key.subkeys():
        try:
            walk(s, depth+1)
        except Exception:
            pass

walk(reg.root())
