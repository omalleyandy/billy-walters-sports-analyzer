import os
import json
import glob

base = os.path.join(os.path.dirname(__file__), "..", "exports")
paths = sorted(glob.glob(os.path.join(base, "*.*")), key=os.path.getmtime, reverse=True)
print(
    json.dumps(
        {
            "exports": [
                {"file": p, "mb": round(os.path.getsize(p) / 1_000_000, 3)}
                for p in paths
            ]
        },
        indent=2,
    )
)
