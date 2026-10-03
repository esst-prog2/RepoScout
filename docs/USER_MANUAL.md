# RepoScout User Manual

RepoScout searches GitHub for repositories matching a keyword, ranks them by stars, classifies each by recent activity, and gives you both a quick terminal summary and a CSV you can open in a spreadsheet.

## Quick Start

```
pip install .
reposcout search "expense tracker"
```

First run with no token set up will prompt you to paste one in (leave blank to skip — it'll still work, just with a lower rate limit). Results print in your terminal, and a `expense-tracker-report.csv` file appears in your current folder.

That's it. Read on below for details on tokens, `--refresh`, and where files are stored.

## Installation

RepoScout requires Python 3.10 or newer.

From the project directory, install it with:

```
pip install .
```

This registers `reposcout` as a command you can run from anywhere in your terminal — you don't need to be in the project directory afterward, and you don't need to type `python` in front of it.

To uninstall later:

```
pip uninstall reposcout
```

## Providing a GitHub token

GitHub's search endpoint — the one RepoScout uses — limits how many requests per *minute* you can make: 10/minute without credentials, 30/minute with a free personal access token. This limit resets every minute, so if you hit it, waiting briefly is often enough on its own — but a token still makes repeated searching more comfortable if you're searching a lot in a short span.

There are two ways to provide one:

**Option 1 — set the `GITHUB_TOKEN` environment variable** (best if you already know how):

```
# macOS/Linux
export GITHUB_TOKEN=ghp_your_token_here

# Windows PowerShell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

**Option 2 — let RepoScout ask you.** The first time you run a search without `GITHUB_TOKEN` set and without a token saved from before, RepoScout will prompt you to paste one in. Typing or pasting shows `*` for each character (so you can see something was received, without ever revealing the token itself) — the same idea as a typical password field. If you provide one, it's saved locally so you're never asked again. If you just press Enter without typing anything, RepoScout remembers that too, and won't ask again — it'll just use the lower, unauthenticated rate limit until you decide to add a token later.

You can create a personal access token at **github.com → Settings → Developer settings → Personal access tokens**. No special permissions/scopes are required for public repo search.

If RepoScout ever tells you your saved token is invalid or expired, it will immediately offer to let you enter a replacement — you don't need to find or edit any files by hand.

## Searching

The basic command is:

```
reposcout search "<keyword>"
```

For example:

```
reposcout search "expense tracker"
```

This prints a ranked table of the top 50 matching repositories (by stars), a one-line summary, and writes a CSV report.

Repeat searches for the same keyword are served from a local cache for 24 hours, so they return instantly and don't use up your GitHub request quota. If you want to force a fresh fetch before the cache expires (for example, if you know something changed recently), add `--refresh`:

```
reposcout search "expense tracker" --refresh
```

You'll almost never need `--refresh` in everyday use — it's just there for the rare case you want current data right now.

## What the output looks like

**Terminal table** — one row per matching repository, ranked by stars:

```
#  Repository        Stars  Last Commit  Language  Bucket
1  someuser/repo-a    1204  2026-08-30   Python    active
2  someuser/repo-b     980  2025-11-02   JS        stale
```

Each repository is classified into one of three activity buckets, based on how long ago it was last pushed to:

- **active** — pushed within the last 3 months
- **slowing** — pushed 3–12 months ago
- **stale** — pushed 12 or more months ago

Below the table, a one-line verdict summarizes the results, for example:

```
42 repos found, 6 active in the last 3 months — most recent entrant pushed 2 weeks ago
```

If GitHub reports more matches than the 50 RepoScout fetches, the verdict says so explicitly (e.g. "Showing top 50 of 3,241 matching repos...") rather than implying the 50 shown is everything that matched.

**CSV export** — a file named after your search keyword, written in the directory you ran the command from. For example, searching `"expense tracker"` produces `expense-tracker-report.csv` in your current folder. It contains the same rows and columns as the terminal table, plus a repository URL column, ready to open directly in Excel, Google Sheets, or Numbers.

## Where your data is stored

RepoScout stores two small files outside the project folder, in locations standard for your operating system (handled automatically — you shouldn't need to find these yourself in normal use):

- **Cached search results** — one file per search keyword, kept for 24 hours, so repeat searches don't re-query GitHub.
- **Your saved GitHub token** (if you provided one) — kept in a separate local config file, not inside the cache.

Both live under your user profile (for example, under `AppData` on Windows, or `~/.cache` and `~/.config` on Linux/macOS) and are private to your account. Nothing is ever sent anywhere except to GitHub's own API.
