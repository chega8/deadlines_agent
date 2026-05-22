#!/usr/bin/env python3
"""Менеджер дедлайнов для агента Grisha.

Единственная точка изменения study/deadlines.json. Атомарная запись (tmp + os.replace).
Все команды выводят JSON в stdout — агент парсит и формулирует ответ.

Usage:
    deadlines.py add   --title T --course C --due YYYY-MM-DD [--priority high|med|low] [--tags a,b]
    deadlines.py done  <id>
    deadlines.py drop  <id>
    deadlines.py move  <id> --due YYYY-MM-DD
    deadlines.py list  [--scope today|week|all|overdue|open] [--course C]
    deadlines.py get   <id>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

HOME = Path(os.environ.get("PICOCLAW_HOME", Path.home() / ".picoclaw"))
STATE = HOME / "workspace" / "study" / "deadlines.json"

EMPTY = {"version": 1, "next_id": 1, "items": []}


def load() -> dict:
    if not STATE.exists():
        STATE.parent.mkdir(parents=True, exist_ok=True)
        save(EMPTY)
        return json.loads(json.dumps(EMPTY))
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".deadlines.", suffix=".json", dir=STATE.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, STATE)
    except Exception:
        os.unlink(tmp)
        raise


def find(items: list, item_id: str) -> dict | None:
    for it in items:
        if it["id"] == item_id:
            return it
    return None


def out(payload: dict, code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


def parse_due(s: str) -> str:
    # validate
    datetime.strptime(s, "%Y-%m-%d")
    return s


def days_until(due: str) -> int:
    d = datetime.strptime(due, "%Y-%m-%d").date()
    return (d - date.today()).days


def cmd_add(args) -> None:
    data = load()
    new_id = f"d{data['next_id']}"
    data["next_id"] += 1
    item = {
        "id": new_id,
        "title": args.title,
        "course": args.course,
        "due": parse_due(args.due),
        "priority": args.priority,
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
        "status": "open",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "closed_at": None,
    }
    data["items"].append(item)
    save(data)
    item["days_until"] = days_until(item["due"])
    out({"ok": True, "item": item})


def _close(item_id: str, new_status: str) -> None:
    data = load()
    it = find(data["items"], item_id)
    if not it:
        out({"ok": False, "error": f"id {item_id} not found"}, 1)
    if it["status"] != "open":
        out({"ok": False, "error": f"id {item_id} already {it['status']}", "item": it}, 1)
    it["status"] = new_status
    it["closed_at"] = datetime.now().isoformat(timespec="seconds")
    save(data)
    out({"ok": True, "item": it})


def cmd_done(args) -> None:
    _close(args.id, "done")


def cmd_drop(args) -> None:
    _close(args.id, "dropped")


def cmd_move(args) -> None:
    data = load()
    it = find(data["items"], args.id)
    if not it:
        out({"ok": False, "error": f"id {args.id} not found"}, 1)
    it["due"] = parse_due(args.due)
    save(data)
    it["days_until"] = days_until(it["due"])
    out({"ok": True, "item": it})


def cmd_get(args) -> None:
    data = load()
    it = find(data["items"], args.id)
    if not it:
        out({"ok": False, "error": f"id {args.id} not found"}, 1)
    it = dict(it)
    if it["status"] == "open":
        it["days_until"] = days_until(it["due"])
    out({"ok": True, "item": it})


def _in_scope(it: dict, scope: str) -> bool:
    if scope == "all":
        return True
    if scope == "open":
        return it["status"] == "open"
    if it["status"] != "open":
        return False
    delta = days_until(it["due"])
    if scope == "today":
        return delta == 0
    if scope == "week":
        return 0 <= delta <= 7
    if scope == "overdue":
        return delta < 0
    return True


def cmd_list(args) -> None:
    data = load()
    items = data["items"]
    items = [it for it in items if _in_scope(it, args.scope)]
    if args.course:
        items = [it for it in items if it["course"].lower() == args.course.lower()]
    # Сортировка: open сначала, потом по due
    def key(it):
        return (it["status"] != "open", it["due"])
    items.sort(key=key)
    enriched = []
    for it in items:
        e = dict(it)
        if it["status"] == "open":
            e["days_until"] = days_until(it["due"])
        enriched.append(e)
    out({"ok": True, "scope": args.scope, "course": args.course, "count": len(enriched), "items": enriched})


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add")
    pa.add_argument("--title", required=True)
    pa.add_argument("--course", required=True)
    pa.add_argument("--due", required=True, help="YYYY-MM-DD")
    pa.add_argument("--priority", choices=["high", "med", "low"], default="med")
    pa.add_argument("--tags", default="")
    pa.set_defaults(fn=cmd_add)

    pd = sub.add_parser("done")
    pd.add_argument("id")
    pd.set_defaults(fn=cmd_done)

    pdr = sub.add_parser("drop")
    pdr.add_argument("id")
    pdr.set_defaults(fn=cmd_drop)

    pm = sub.add_parser("move")
    pm.add_argument("id")
    pm.add_argument("--due", required=True)
    pm.set_defaults(fn=cmd_move)

    pg = sub.add_parser("get")
    pg.add_argument("id")
    pg.set_defaults(fn=cmd_get)

    pl = sub.add_parser("list")
    pl.add_argument("--scope", choices=["today", "week", "all", "overdue", "open"], default="open")
    pl.add_argument("--course")
    pl.set_defaults(fn=cmd_list)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
