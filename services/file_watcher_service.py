"""Watch project folders and emit debounced change notifications."""

from PySide6.QtCore import QObject, Signal, QTimer

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover - handled at runtime
    FileSystemEventHandler = object
    Observer = None


class _ProjectEventHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        super().__init__()
        self.watcher = watcher

    def on_any_event(self, event):
        self.watcher.notify_changed(event.src_path)


class FileWatcherService(QObject):
    """Debounced watchdog wrapper for the current project root."""

    _raw_changed = Signal()
    changed = Signal()

    def __init__(self, debounce_ms: int = 500):
        super().__init__()
        self._observer = None
        self._root_path = ""
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(debounce_ms)
        self._debounce.timeout.connect(self.changed.emit)
        self._raw_changed.connect(self._debounce.start)

    def start(self, root_path: str) -> None:
        self.stop()
        if Observer is None:
            return

        self._root_path = root_path
        self._observer = Observer()
        self._observer.schedule(_ProjectEventHandler(self), root_path, recursive=True)
        self._observer.daemon = True
        self._observer.start()

    def stop(self) -> None:
        self._debounce.stop()
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
        self._root_path = ""

    def notify_changed(self, path: str) -> None:
        normalized = path.replace("\\", "/")
        if "/.artmgr/" in normalized or normalized.endswith("/.artmgr"):
            return
        self._raw_changed.emit()
