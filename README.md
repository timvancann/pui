# pui

[![Test](https://github.com/timvancann/pui/actions/workflows/test.yml/badge.svg)](https://github.com/timvancann/pui/actions/workflows/test.yml)

A tiny cross-platform TUI for managing processes listening on ports. Select a process, kill it, move on with your life.

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

## Platform Support

Works without elevated privileges on all platforms.

| Platform | Method |
| -------- | ------ |
| Linux    | lsof   |
| macOS    | lsof   |
| Windows  | psutil |

---

_Vibe coded with Claude Code because... why not, right?_
