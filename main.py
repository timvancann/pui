"""PUI - Process Port Manager: A TUI for managing processes listening on ports."""

import psutil
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Label, Static


def get_port_processes() -> list[tuple[int, int, str, str]]:
    """Fetch all processes listening on ports using psutil.

    Returns:
        List of tuples containing (port, pid, process_name, status).
    """
    processes: list[tuple[int, int, str, str]] = []
    seen_ports: set[int] = set()

    try:
        connections = psutil.net_connections(kind="tcp")
    except psutil.AccessDenied:
        return processes

    for conn in connections:
        if conn.status != "LISTEN" or conn.pid is None:
            continue

        port = conn.laddr.port
        if port in seen_ports:
            continue
        seen_ports.add(port)

        try:
            proc = psutil.Process(conn.pid)
            process_name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "unknown"

        processes.append((port, conn.pid, process_name, "LISTEN"))

    return sorted(processes, key=lambda x: x[0])


class ConfirmKillScreen(ModalScreen[bool]):
    """Modal screen for confirming process termination."""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("enter", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "No", show=False),
    ]

    def __init__(self, pid: int, process_name: str, port: int) -> None:
        super().__init__()
        self.pid = pid
        self.process_name = process_name
        self.port = port

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Confirm Kill Process", id="confirm-title"),
            Label(
                f"Kill process '{self.process_name}' (PID: {self.pid}) on port {self.port}?"
            ),
            Label("[y] Yes  [n] No", id="confirm-options"),
            id="confirm-dialog",
        )

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class PortProcessApp(App[None]):
    """A TUI application for managing processes listening on ports."""

    CSS = """
    Screen {
        background: $surface;
    }

    DataTable {
        height: 1fr;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }

    #confirm-dialog {
        align: center middle;
        width: 60;
        height: 9;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #confirm-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #confirm-options {
        text-align: center;
        margin-top: 1;
        color: $text-muted;
    }

    ConfirmKillScreen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("x", "kill_process", "Kill Process"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    TITLE = "PUI - Process Port Manager"

    def __init__(self) -> None:
        super().__init__()
        self.status_message = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the data table with process information."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Port", "PID", "Process Name", "Status")
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the process table with current data."""
        table = self.query_one(DataTable)
        table.clear()

        processes = get_port_processes()

        if not processes:
            self._set_status("No processes listening on ports found (may require sudo)")
            return

        for port, pid, name, status in processes:
            table.add_row(str(port), str(pid), name, status)

        self._set_status(f"Found {len(processes)} process(es) listening on ports")

    def _set_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_message = message
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(message)

    def action_refresh(self) -> None:
        """Refresh the process list."""
        self._refresh_table()

    def action_cursor_down(self) -> None:
        """Move cursor down in the table."""
        table = self.query_one(DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the table."""
        table = self.query_one(DataTable)
        table.action_cursor_up()

    @work
    async def action_kill_process(self) -> None:
        """Kill the currently selected process."""
        table = self.query_one(DataTable)

        if table.row_count == 0:
            self._set_status("No processes to kill")
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_data = table.get_row(row_key)

        port = int(row_data[0])
        pid = int(row_data[1])
        process_name = str(row_data[2])

        confirmed = await self.push_screen_wait(
            ConfirmKillScreen(pid, process_name, port)
        )

        if confirmed:
            self._kill_process(pid, process_name)

    def _kill_process(self, pid: int, process_name: str) -> None:
        """Terminate a process by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            self._set_status(f"Terminated '{process_name}' (PID: {pid})")
            self._refresh_table()
        except psutil.NoSuchProcess:
            self._set_status(f"Process {pid} no longer exists")
            self._refresh_table()
        except psutil.AccessDenied:
            self.notify(
                f"Permission denied: cannot kill '{process_name}' (PID: {pid})",
                severity="error",
                timeout=5,
            )
        except Exception as e:
            self.notify(f"Error killing process: {e}", severity="error", timeout=5)


def main() -> None:
    """Run the PUI application."""
    app = PortProcessApp()
    app.run()


if __name__ == "__main__":
    main()
