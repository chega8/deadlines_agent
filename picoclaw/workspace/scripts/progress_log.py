#!/usr/bin/env python3
"""Лог прогресса и недельная статистика для агента Grisha.

Дописывает строки в study/progress.md. Не редактирует существующие строки.

Usage:
    progress_log.py log     --verb VERB --id ID --note "..."        # generic log line
    progress_log.py session --course C --minutes N [--note "..."]   # учебная сессия
    progress_log.py ping    --id ID --note "..."                    # heartbeat-пинг
    progress_log.py weekly                                          # статистика за 7 дней
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HOME = Path(os.environ.get("PICOCLAW_HOME", Path.home() / ".picoclaw"))
LOG = HOME / "workspace" / "study" / "progress.md"
DEADLINES = HOME / "workspace" / "study" / "deadlines.json"

SESSIONS_HEADER = "## Sessions"
ACTIONS_HEADER = "## Actions"

TEMPLATE = f"""# Study Progress Log

Машинно-парсимый append-only лог. Формат строк:

- `- YYYY-MM-DD HH:MM | <verb> | <id_or_dash> | <note>` — в секции Actions
- `- YYYY-MM-DD HH:MM | session | <course> | <minutes>m | <note>` — в секции Sessions

{ACTIONS_HEADER}

{SESSIONS_HEADER}
"""


def ensure_log() -> None:
    if not LOG.exists():
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text(TEMPLATE, encoding="utf-8")


def append_in_section(line: str, header: str) -> None:
    ensure_log()
    text = LOG.read_text(encoding="utf-8")
    if header not in text:
        text += f"\n{header}\n"
    # Найти позицию следующего заголовка (## ...) после нашего, либо конец файла
    idx = text.index(header) + len(header)
    rest = text[idx:]
    m = re.search(r"\n##\s", rest)
    insert_at = idx + (m.start() if m else len(rest))
    # Убедиться, что перед вставкой есть \n
    prefix = text[:insert_at].rstrip() + "\n"
    suffix = text[insert_at:]
    new = prefix + line.rstrip() + "\n" + suffix
    LOG.write_text(new, encoding="utf-8")


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def out(payload: dict, code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


def cmd_log(args) -> None:
    line = f"- {ts()} | {args.verb} | {args.id or '-'} | {args.note or ''}"
    append_in_section(line, ACTIONS_HEADER)
    out({"ok": True, "line": line})


def cmd_session(args) -> None:
    note = args.note or ""
    line = f"- {ts()} | session | {args.course} | {args.minutes}m | {note}"
    append_in_section(line, SESSIONS_HEADER)
    out({"ok": True, "line": line})


def cmd_ping(args) -> None:
    line = f"- {ts()} | ping | {args.id} | {args.note or ''}"
    append_in_section(line, ACTIONS_HEADER)
    out({"ok": True, "line": line})


SESSION_RE = re.compile(
    r"^- (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} \| session \| ([^|]+) \| (\d+)m"
)
ACTION_RE = re.compile(
    r"^- (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} \| (\w+) \| (\S+) \|"
)


def cmd_weekly(args) -> None:
    ensure_log()
    text = LOG.read_text(encoding="utf-8")
    today = date.today()
    week_ago = today - timedelta(days=6)

    by_course: dict[str, int] = {}
    closed = 0
    added = 0
    dropped = 0
    moved = 0
    sessions = 0

    for raw in text.splitlines():
        m = SESSION_RE.match(raw.strip())
        if m:
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            if week_ago <= d <= today:
                course = m.group(2).strip()
                mins = int(m.group(3))
                by_course[course] = by_course.get(course, 0) + mins
                sessions += 1
            continue
        m = ACTION_RE.match(raw.strip())
        if m:
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            if week_ago <= d <= today:
                verb = m.group(2)
                if verb == "done":
                    closed += 1
                elif verb == "add":
                    added += 1
                elif verb == "drop":
                    dropped += 1
                elif verb == "move":
                    moved += 1

    # Текущие висящие
    open_now = 0
    if DEADLINES.exists():
        data = json.loads(DEADLINES.read_text(encoding="utf-8"))
        open_now = sum(1 for it in data["items"] if it["status"] == "open")

    out({
        "ok": True,
        "from": str(week_ago),
        "to": str(today),
        "sessions": sessions,
        "minutes_by_course": by_course,
        "total_minutes": sum(by_course.values()),
        "closed": closed,
        "added": added,
        "dropped": dropped,
        "moved": moved,
        "open_now": open_now,
    })


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("log")
    pl.add_argument("--verb", required=True)
    pl.add_argument("--id", default="")
    pl.add_argument("--note", default="")
    pl.set_defaults(fn=cmd_log)

    ps = sub.add_parser("session")
    ps.add_argument("--course", required=True)
    ps.add_argument("--minutes", type=int, required=True)
    ps.add_argument("--note", default="")
    ps.set_defaults(fn=cmd_session)

    pp = sub.add_parser("ping")
    pp.add_argument("--id", required=True)
    pp.add_argument("--note", default="")
    pp.set_defaults(fn=cmd_ping)

    pw = sub.add_parser("weekly")
    pw.set_defaults(fn=cmd_weekly)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
