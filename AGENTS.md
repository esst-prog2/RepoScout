# AGENTS.md — Planning Log

This file tracks planning decisions and progress for RepoScout across sessions. Append new entries at the bottom; don't rewrite history.

## 2026-09-22

- Repo currently contains only `README.md` (the project spec) — no code yet.
- README defines the first-useful-version scope: a CLI (`reposcout search "<keyword>"`) that queries GitHub's Search API, fetches stars/last-commit-date/primary-language per repo, buckets repos by activity (active/slowing/stale), prints a terminal summary, exports a CSV, and caches results per keyword for 24 hours.
- Explicitly out of scope this term: browser UI, AI-generated summaries, saved-search tracking/alerts, cross-referencing other sources, cloning repos, multi-user auth.
- Next step (not yet started): scaffold the project (language/framework choice, GitHub API client, CLI entrypoint, cache layer, CSV writer).

## 2026-09-22 (later)

- Verified Node.js (v24.21.0) and npm (11.19.0) were already installed — no install needed.
- Installed [OpenSpec](https://openspec.dev) CLI globally via npm. First attempt (`npm install -g openspec`) pulled an unrelated placeholder package (empty, v0.0.0, no binary) — uninstalled it. Correct package is `@fission-ai/openspec@latest`; installed that instead (CLI v1.13.1).
- Ran `openspec init --tools claude` in the repo root. This created:
  - `openspec/config.yaml` (schema: spec-driven) plus `openspec/specs/` and `openspec/changes/archive/` directories
  - `.claude/commands/opsx/*.md` and `.claude/skills/openspec-*/SKILL.md` — Claude Code slash commands/skills for the OpenSpec workflow (propose, update, apply, archive, explore, sync)
- Nothing committed yet — `openspec/`, `.claude/`, and `AGENTS.md` are untracked in git.
- Next step: decide whether to start the actual project scaffold via OpenSpec's proposal workflow (`/opsx:propose`) or scaffold directly, then commit the OpenSpec setup files.
