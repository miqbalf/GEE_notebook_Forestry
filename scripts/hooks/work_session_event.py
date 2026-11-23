#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

EVENTS = {
    "SessionStart": "start",
    "UserPromptSubmit": "prompt",
    "PostToolUse": "coding",
    "Stop": "stop",
    "SessionEnd": "end",
}
CODING_THROTTLE_SECONDS = 60
TIMEOUT_SECONDS = 2.0
DEFAULT_URL = "https://treeo.cloud"
PATH = "/v1/work/session-event"


def stamp_dir() -> Path:
    return Path.home() / ".cache" / "treeo-work"


def _git(cwd: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except Exception:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def repo_and_branch(cwd: str) -> tuple[str, str]:
    if not cwd:
        return "", ""
    url = _git(cwd, "remote", "get-url", "origin")
    name = re.split(r"[/:]", url.rstrip("/"))[-1] if url else ""
    if name.endswith(".git"):
        name = name[:-4]
    return name, _git(cwd, "branch", "--show-current")


def build_payload(data: dict, now: datetime | None = None, lookup=repo_and_branch) -> dict | None:
    event = EVENTS.get(str(data.get("hook_event_name") or ""))
    session_id = str(data.get("session_id") or "")
    if not event or not session_id:
        return None
    repo, branch = lookup(str(data.get("cwd") or ""))
    at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    return {"session_id": session_id, "event": event, "at": at, "repo": repo, "branch": branch}


def should_send_coding(session_id: str, now: float | None = None, directory: Path | None = None) -> bool:
    current = time.time() if now is None else now
    base = directory or stamp_dir()
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)[:128]
    stamp = base / f"{safe}.coding"
    try:
        if stamp.exists() and current - stamp.stat().st_mtime < CODING_THROTTLE_SECONDS:
            return False
        base.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        os.utime(stamp, (current, current))
    except Exception:
        return True
    return True


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def send(payload: dict, token: str, base_url: str, timeout: float = TIMEOUT_SECONDS) -> None:
    request = urllib.request.Request(
        base_url.rstrip("/") + PATH,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(NoRedirect)
    with opener.open(request, timeout=timeout) as response:
        response.read()


def handle(data: dict, env=None, directory: Path | None = None, poster=send, lookup=repo_and_branch) -> bool:
    env = os.environ if env is None else env
    token = env.get("TREEO_PAT", "")
    if not token:
        return False
    if EVENTS.get(str(data.get("hook_event_name") or "")) == "coding":
        if not should_send_coding(str(data.get("session_id") or ""), directory=directory):
            return False
    payload = build_payload(data, lookup=lookup)
    if payload is None:
        return False
    poster(payload, token, env.get("TREEO_HERMES_URL") or DEFAULT_URL)
    return True


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict) or not os.environ.get("TREEO_PAT"):
            os._exit(0)
        if hasattr(os, "fork"):
            if os.fork() != 0:
                os._exit(0)
            try:
                os.setsid()
                devnull = os.open(os.devnull, os.O_RDWR)
                for fd in (0, 1, 2):
                    os.dup2(devnull, fd)
            except Exception:
                pass
        handle(data)
    except BaseException:
        pass
    os._exit(0)


if __name__ == "__main__":
    main()
