# pui

A tiny TUI for managing processes listening on ports. Select a process, kill it, move on with your life.

## Install

```bash
uvx --from git+https://github.com/timvancann/pui.git pui
```

Or install globally:

```bash
uv tool install git+https://github.com/timvancann/pui.git
```

Then just run `pui`.

## Usage

| Key   | Action                |
| ----- | --------------------- |
| `j/k` | Navigate up/down      |
| `x`   | Kill selected process |
| `r`   | Refresh               |
| `q`   | Quit                  |

## Notes

- **Linux**: Works without elevated privileges
- **macOS**: Requires `sudo pui` to list connections
- **Windows**: Requires running as Administrator

---

_Vibe coded with Claude Code because... why not, right?_
