# climate-control

Home Assistant custom integration for smart, family-friendly heating control.

## Agent skills

### Issue tracker

Specs and tickets live as local markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Checks

Run from the root of any worktree on Windows (all Python tooling runs in WSL):

```powershell
wsl -d RSLinux-24.04 -- ./scripts/check                          # ruff check, ruff format --check, mypy, all tests
wsl -d RSLinux-24.04 -- ./scripts/check tests/test_main_entry.py # only pytest, any pytest arguments
```

- `scripts/check` needs `uv` in `~/.local/bin` (WSL). It syncs a per-worktree virtualenv under `~/.cache/climate-control/venvs/<hash of path>` and uses the uv cache in `~/.cache/climate-control/uv`, so worktrees can run it concurrently. CI (`.github/workflows/ci.yml`) runs the same script plus hassfest and HACS validation.
- Tests use `pytest-homeassistant` (the official successor of `pytest-homeassistant-custom-component`), pinned to the Home Assistant version in `pyproject.toml`. Simulated TRVs for scenario tests: `tests/simulated_trv.py` (fixture `simulated_trvs`).
- Git does not work inside WSL in worktrees (`.git` holds a Windows path): run git from Windows.
- WSL DNS: in `RSLinux-24.04` the WSL resolver `10.255.255.254` refuses connections, so `uv sync` fails to resolve hosts when it needs the network (new or changed dependencies). With a warm uv cache `scripts/check` works offline. TLS itself is fine; never disable verification. Proper fix (needs sudo): point `/etc/resolv.conf` at the corporate DNS `10.0.2.166` / `10.0.23.159` with `generateResolvConf = false` in `/etc/wsl.conf`. Workaround without sudo, used to bootstrap uv, Python and the cache: run the command in a private mount namespace with its own resolver file:

  ```bash
  unshare --user --map-root-user --mount bash -c 'printf "nameserver 10.0.2.166\nnameserver 10.0.23.159\n" > /tmp/cc-resolv.conf && mount --bind /tmp/cc-resolv.conf /etc/resolv.conf && UV_CACHE_DIR=$HOME/.cache/climate-control/uv ~/.local/bin/uv lock && ./scripts/check'
  ```

  This fills the shared uv cache; afterwards `scripts/check` works normally in every worktree.
