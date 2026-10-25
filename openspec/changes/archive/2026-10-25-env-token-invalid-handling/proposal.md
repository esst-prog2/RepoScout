# Proposal

## Why

When GitHub rejects a token that came from the `GITHUB_TOKEN` environment variable, RepoScout currently treats it like a rejected *saved* token: it says "Your saved GitHub token appears invalid or expired", prompts for a replacement, and saves that replacement to the config file. But the environment variable takes precedence over the saved token (per the `github-auth` "Token resolution order" requirement), so on the next run the same bad env-var token is used again and the user is re-prompted every single run. The message is also wrong: nothing saved was rejected. Found during HW6 review 1 and carried forward as an open issue.

## What Changes

- When a token rejected by GitHub came from the `GITHUB_TOKEN` environment variable, RepoScout SHALL NOT prompt for a replacement and SHALL NOT write anything to the config file.
- Instead it prints a clear message that the token in the `GITHUB_TOKEN` environment variable is invalid or expired and tells the user to update or unset that variable, then exits with code `1` (the generic-error code).
- The existing recovery for a rejected *saved* token (inform, offer re-entry, overwrite the saved token, retry once) is unchanged.
- `docs/USER_MANUAL.md` gains one sentence explaining what happens when the env-var token is invalid.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `github-auth`: the "Invalid or expired saved token recovery" requirement gains a scenario stating that a rejected **environment-variable** token is reported with a fix-the-variable message and exit code `1`, without prompting or saving.

## Impact

- **Code:** `reposcout/auth.py` (a way to tell whether the token came from the env var, plus the new message) and `reposcout/cli.py` (`_fetch_with_token_recovery()` branches on the token's source).
- **Tests:** `tests/test_cli.py` (new CLI-level test for the env-var case; existing saved-token recovery tests must still pass), `tests/test_auth.py` if a new helper is added.
- **Docs:** `docs/USER_MANUAL.md` token section.
- **No** new dependencies, no change to exit codes `2`/`3`, no change to token resolution order.
