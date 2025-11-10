#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, os
from typing import Any, Dict, List, Tuple

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "commands.json")
ORDER_HINT = ["hooks.", "espn.", "massey.", "overtime."]

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)

def validate(doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if "version" not in doc or not isinstance(doc["version"], str):
        errs.append("missing/invalid: version")
    if "commands" not in doc or not isinstance(doc["commands"], list):
        errs.append("missing/invalid: commands[]")
    else:
        seen = set()
        for i, c in enumerate(doc["commands"]):
            if "id" not in c: errs.append(f"commands[{i}] missing id")
            else:
                if c["id"] in seen: errs.append(f"duplicate id: {c['id']}")
                seen.add(c["id"])
            if "cwd" not in c: errs.append(f"{c.get('id','?')} missing cwd")
            if "cmd" not in c or not isinstance(c["cmd"], list):
                errs.append(f"{c.get('id','?')} missing cmd[]")
    return (len(errs) == 0, errs)

def bump_version(v: str, mode: str) -> str:
    parts = [int(p) for p in v.split(".")]
    while len(parts) < 3: parts.append(0)
    major, minor, patch = parts[:3]
    if mode == "major": major, minor, patch = major+1, 0, 0
    elif mode == "minor": minor, patch = minor+1, 0
    elif mode == "patch": patch += 1
    else: raise ValueError("mode must be major|minor|patch")
    return f"{major}.{minor}.{patch}"

def merge(existing: List[Dict[str, Any]], updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    idx = {c["id"]: i for i, c in enumerate(existing)}
    result = existing[:]
    for u in updates:
        uid = u["id"]
        if uid in idx:
            # update in place; shallow merge of top-level keys
            i = idx[uid]
            merged = result[i].copy()
            merged.update(u)
            result[i] = merged
        else:
            result.append(u)
    # stable order: group by ORDER_HINT prefixes, then alphabetical within group
    def keyfunc(cmd: Dict[str, Any]) -> Tuple[int, str]:
        for pos, prefix in enumerate(ORDER_HINT):
            if cmd["id"].startswith(prefix): return (pos, cmd["id"])
        return (len(ORDER_HINT), cmd["id"])
    return sorted(result, key=keyfunc)

def main():
    ap = argparse.ArgumentParser(description="Manage codex commands.json")
    ap.add_argument("--file", default=DEFAULT_PATH, help="Path to commands.json")
    ap.add_argument("--add-file", help="JSON file with commands[] to add/update")
    ap.add_argument("--bump", choices=["major","minor","patch"], help="Bump version")
    ap.add_argument("--set-meta-note", help="Set/replace meta.notes")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    doc = load_json(args.file)
    ok, errs = validate(doc)
    if not ok:
        print(json.dumps({"status":"invalid","errors":errs}, indent=2))
        sys.exit(1)

    changed = False

    if args.add_file:
        upd_doc = load_json(args.add_file)
        updates = upd_doc["commands"] if "commands" in upd_doc else upd_doc
        doc["commands"] = merge(doc["commands"], updates)
        changed = True

    if args.bump:
        doc["version"] = bump_version(doc["version"], args.bump)
        changed = True

    if args.set_meta_note:
        meta = doc.get("meta", {})
        meta["notes"] = args.set_meta_note
        doc["meta"] = meta
        changed = True

    ok2, errs2 = validate(doc)
    if not ok2:
        print(json.dumps({"status":"invalid_after_merge","errors":errs2}, indent=2))
        sys.exit(1)

    if args.dry_run or not changed:
        print(json.dumps({"status":"ok","changed":changed,"doc":doc}, indent=2))
        return

    save_json(args.file, doc)
    print(json.dumps({"status":"saved","file":args.file,"version":doc["version"]}, indent=2))

if __name__ == "__main__":
    main()
