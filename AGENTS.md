# Repository Guidelines

This repo contains a Vim plugin for browsing Hacker News inside Vim. Use this guide to contribute changes consistently and safely.

## Project Structure & Module Organization
- `plugin/` — entrypoint, defines `:HackerNews` and default options.
- `ftplugin/` — buffer-local logic and Python integration (`hackernews.vim`, `hackernews.py`).
- `syntax/` — syntax highlighting for `.hackernews` buffers.
- `doc/` — help file (`doc/hackernews.txt`). Run `:helptags doc` after edits.
- `tests.vader` — Vader test suite.
- `screenshots/` — static assets for README.

## Build, Test, and Development Commands
- Lint Python: `flake8 ftplugin/hackernews.py`
- Run tests (requires `vader.vim` on runtimepath):
  - Clone: `git clone https://github.com/junegunn/vader.vim`
  - Test: `vim -Nu NONE -c 'set rtp+=vader.vim' -c 'set rtp+=.' -c 'Vader! tests.vader' -c 'qa!'`
- Quick load plugin locally: `vim -Nu NONE -c 'set rtp+=.' -c 'HackerNews'`

## Coding Style & Naming Conventions
- Vimscript: 2 spaces indent, script‑local helpers (`s:`), public command `HackerNews` only.
- Python: follow `flake8` defaults; 4 spaces indent, keep lines ≤ 88 chars; prefer clear names over brevity.
- Text width: the UI wraps to 80 columns; keep rendered content mindful of 80‑col buffers.
- Files: snake_case for Python, lowercase for Vimscript filenames (`plugin/hackernews.vim`).

## Testing Guidelines
- Framework: [Vader.vim]. Add targeted blocks to `tests.vader` mirroring existing style (Execute/Do/Then).
- Coverage: include tests for new mappings, commands, and buffer rendering edge cases (folding, code blocks, wide lines).
- Network: tests should not depend on live APIs beyond what CI already uses; mock or gate as needed.

## Commit & Pull Request Guidelines
- Commits: imperative mood and scoped message, e.g., `ftplugin: handle markdown code blocks`.
- Include brief rationale and user‑visible impact in the body.
- PRs: describe change, usage notes, and screenshots for UI changes; link issues; note any API/network considerations and timeouts.
- Update `doc/hackernews.txt`, `README.md`, and `CHANGES` when behavior or commands change.

## Security & Configuration Tips
- External services: API calls hit `node-hnapi` and a markdown service; handle timeouts and errors gracefully.
- Compatibility: support both `+python` and `+python3` builds as in current code paths.

