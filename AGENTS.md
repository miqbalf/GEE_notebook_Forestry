# AGENTS.md

## Work progress report (Treeo, all staff)
Every Claude Code session in this repo is part of Treeo work progress, which HR and the board read.
- Setup once per machine: connect the `treeo` MCP server (https://treeo.cloud/mcp/sse, see hermes-ai `install_claude/MCP_SETUP.md`) and set `TREEO_PAT` in your shell profile. The session hook in `.claude/settings.json` (`scripts/hooks/work_session_event.py`) then records session start, stop and edit times. Without `TREEO_PAT` it does nothing.
- At the end of a session that changed this repo, call `mcp__treeo__work_report` once with the repo name, the branch, a 2-5 sentence summary (what changed and why), the commit SHAs, and the Claude Code session id when known.
- Never put secrets, customer data or salary figures in the summary.
- If the treeo MCP is not connected, say so at the end of the session instead of calling it.
