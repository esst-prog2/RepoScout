# Tasks

## 1. Reproduce first

- [x] 1.1 Add a CLI-level test in `tests/test_cli.py`: `GITHUB_TOKEN` set to a bad token, GitHub mocked to return 401; assert exit code `1`, the message names `GITHUB_TOKEN` and says to update or unset it, the prompt (`pwinput`) is never called, no config file is written, and exactly one API call is made. Run it and verify it fails against the current code (it currently prompts).

## 2. Implementation

- [x] 2.1 Add `token_from_env()` and `invalid_env_token_message()` to `reposcout/auth.py`; verify with unit tests in `tests/test_auth.py` (env var set → `True`, unset or empty → `False`; message contains `GITHUB_TOKEN`).
- [x] 2.2 In `cli._fetch_with_token_recovery()`, after the `token is None` guard, raise `GitHubAPIError(auth.invalid_env_token_message())` when `auth.token_from_env()`; verify the test from 1.1 now passes.
- [x] 2.3 Make the existing saved-token recovery CLI tests (`test_rejected_token_is_replaced_and_search_retried`, `test_rejected_replacement_token_exits_cleanly`) clear `GITHUB_TOKEN` so they don't depend on the machine's environment; verify they still pass unchanged otherwise.

## 3. Docs and verification

- [x] 3.1 Update `docs/USER_MANUAL.md` token section: if the token in `GITHUB_TOKEN` is invalid or expired, RepoScout says so and asks you to update or unset the variable (no prompt, nothing saved); verify by reading the rendered section.
- [x] 3.2 Run the full suite (`pytest`) and `openspec validate env-token-invalid-handling --strict`; verify both pass.
