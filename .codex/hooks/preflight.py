import os, json, subprocess, sys
tool_dir = os.path.join(os.path.dirname(__file__), "tools", "devtools-scout")
def run(cmd):
    return subprocess.run(cmd, cwd=tool_dir, capture_output=True, text=True)
uv = run(["uv","run","python","-c","print('ok')"])
chrom = run(["uv","run","python","-c","from playwright.sync_api import sync_playwright as sp; print('chrom-ok')"])
ok = (uv.returncode==0) and (chrom.returncode==0)
print(json.dumps({"uv_ok": uv.returncode==0, "chromium_env_ok": chrom.returncode==0, "tool_dir": tool_dir}, indent=2))
sys.exit(0 if ok else 1)