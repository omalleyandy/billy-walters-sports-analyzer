import os
import json
import glob

base = os.path.join(os.path.dirname(__file__), "tools", "devtools-scout", "exports")
paths = sorted(glob.glob(os.path.join(base, "*.*")), key=os.path.getmtime, reverse=True)
manifest = [{"file": p, "size_bytes": os.path.getsize(p)} for p in paths]
print(json.dumps({"exports": manifest}, indent=2))
