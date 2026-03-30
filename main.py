import json
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from PySide6.QtCore import QDateTime, QSize, Qt, QUrl
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyle,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView


APP_NAME = "Neon Browser"
ORG_NAME = "HiHippo"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "neon_browser_data"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
SESSION_FILE = DATA_DIR / "session.json"
CLOSED_TABS_FILE = DATA_DIR / "closed_tabs.json"
HOMEPAGE_FILE = DATA_DIR / "homepage.html"

DEFAULT_SETTINGS = {
    "homepage": "",
    "search_engine": "https://duckduckgo.com/?q={}",
    "restore_session": True,
    "dark_mode": True,
}


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    html = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Neon</title>
  <style>
    :root {
      color-scheme: dark;
      --bg1: #0b1020;
      --bg2: #111827;
      --card: rgba(17, 24, 39, 0.72);
      --border: rgba(255, 255, 255, 0.10);
      --text: #e5eefc;
      --muted: #9fb0cc;
      --accent: #67e8f9;
      --accent2: #a78bfa;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; font-family: Segoe UI, Arial, sans-serif; }
    body {
      background:
        radial-gradient(circle at top left, rgba(103, 232, 249, 0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(167, 139, 250, 0.16), transparent 26%),
        linear-gradient(135deg, var(--bg1), var(--bg2));
      color: var(--text);
      display: grid;
      place-items: center;
      overflow: hidden;
    }
    .wrap { width: min(980px, calc(100vw - 32px)); }
    .hero {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 28px;
      padding: 42px;
      backdrop-filter: blur(16px);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }
    .brand { display: flex; align-items: center; gap: 14px; }
    .logo {
      width: 54px;
      height: 54px;
      border-radius: 16px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      box-shadow: 0 10px 30px rgba(103, 232, 249, 0.25);
    }
    h1 { margin: 0; font-size: 2.3rem; }
    .sub { margin: 8px 0 0; color: var(--muted); }
    .search {
      margin-top: 28px;
      display: flex;
      gap: 10px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 12px;
      border-radius: 20px;
    }
    input {
      flex: 1;
      min-width: 0;
      background: transparent;
      border: 0;
      color: var(--text);
      outline: none;
      font-size: 1.05rem;
      padding: 10px 12px;
    }
    button, .chip {
      border: 0;
      border-radius: 14px;
      padding: 12px 16px;
      font-size: 0.98rem;
      cursor: pointer;
      text-decoration: none;
      color: #08111f;
      background: linear-gradient(135deg, var(--accent), #c4b5fd);
      font-weight: 700;
    }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    .chip {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text);
      border: 1px solid var(--border);
    }
    .grid {
      margin-top: 22px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }
    .card {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
      min-height: 96px;
    }
    .card h3 { margin: 0 0 8px; font-size: 1rem; }
    .card p { margin: 0; color: var(--muted); font-size: 0.92rem; line-height: 1.45; }
    .footer { margin-top: 18px; color: var(--muted); font-size: 0.9rem; }
    @media (max-width: 860px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .hero { padding: 26px; } }
    @media (max-width: 560px) { .grid { grid-template-columns: 1fr; } .search { flex-direction: column; } }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="brand">
        <div class="logo"></div>
        <div>
          <h1>Neon</h1>
          <p class="sub">browse the web</p>
        </div>
      </div>

      <form class="search" onsubmit="go(event)">
        <input id="q" autocomplete="off" placeholder="Search the web!" />
        <button type="submit">Go</button>
      </form>

      <div class="actions">
        <a class="chip" href="https://www.youtube.com/" target="_blank" rel="noopener">YouTube</a>
        <a class="chip" href="https://www.wikipedia.org/" target="_blank" rel="noopener">Wikipedia</a>
        <a class="chip" href="https://www.github.com/" target="_blank" rel="noopener">GitHub</a>
      </div>

      <div class="grid">
        <div class="card"><h3>Tabs</h3><p>Keep multiple pages open and switch quickly.</p></div>
        <div class="card"><h3>Bookmarks</h3><p>Save favorite sites and reopen them later.</p></div>
        <div class="card"><h3>History</h3><p>Find pages you visited without digging around.</p></div>
        <div class="card"><h3>Downloads</h3><p>Track files your browser saves.</p></div>
      </div>

      <div> Browser made by RyGuy1234hi </div>
    </div>
  </div>

  <script>
    function go(event) {
      event.preventDefault();
      const q = document.getElementById('q').value.trim();
      if (!q) return;
      if (/^(https?:\/\/|file:\/\/|about:)/i.test(q) || q.includes('.') || q.includes(':')) {
        window.location.href = q.startsWith('http') ? q : 'https://' + q;
      } else {
        window.location.href = 'https://duckduckgo.com/?q=' + encodeURIComponent(q);
      }
    }
  </script>
</body>
</html>
'''
    HOMEPAGE_FILE.write_text(html, encoding="utf-8")

    for path, default in (
        (BOOKMARKS_FILE, []),
        (HISTORY_FILE, []),
        (SETTINGS_FILE, DEFAULT_SETTINGS),
        (SESSION_FILE, []),
        (CLOSED_TABS_FILE, []),
    ):
        if not path.exists():
            path.write_text(json.dumps(default, indent=2), encoding="utf-8")


def load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def now_iso() -> str:
    return QDateTime.currentDateTime().toString(Qt.ISODateWithMs)


def homepage_url() -> str:
    return HOMEPAGE_FILE.resolve().as_uri()


def smart_url_or_search(text: str, search_template: str) -> QUrl:
    text = text.strip()
    if not text:
        return QUrl("about:blank")

    parsed = urlparse(text)
    looks_like_url = (
        parsed.scheme in {"http", "https", "file", "about"}
        or text.startswith("localhost")
        or "." in text
        or (":" in text and " " not in text)
    )

    if looks_like_url:
        if not parsed.scheme:
            text = "https://" + text
        return QUrl(text)

    return QUrl(search_template.format(quote_plus(text)))


class BrowserPage(QWebEnginePage):
    def __init__(self, profile: QWebEngineProfile, parent_window):
        super().__init__(profile, parent_window)
        self.parent_window = parent_window

    def createWindow(self, _type):
        tab = self.parent_window.add_tab(QUrl("about:blank"), foreground=True)
        return tab.page()


class BookmarkDialog(QDialog):
    def __init__(self, bookmarks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.resize(700, 460)
        self._all = bookmarks[:]

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search bookmarks...")
        layout.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Title", "URL"])
        layout.addWidget(self.tree)

        row = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.remove_btn = QPushButton("Remove")
        self.copy_btn = QPushButton("Copy URL")
        row.addWidget(self.open_btn)
        row.addWidget(self.remove_btn)
        row.addWidget(self.copy_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.search.textChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.tree.clear()
        q = self.search.text().strip().lower()
        for bm in self._all:
            title = bm.get("title", "Untitled")
            url = bm.get("url", "")
            if q and q not in title.lower() and q not in url.lower():
                continue
            item = QTreeWidgetItem([title, url])
            item.setData(0, Qt.UserRole, bm)
            self.tree.addTopLevelItem(item)
        self.tree.resizeColumnToContents(0)


class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.resize(760, 520)
        self._all = history[:]

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search history...")
        layout.addWidget(self.search)

        self.list = QListWidget()
        layout.addWidget(self.list)

        row = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.clear_btn = QPushButton("Clear History")
        row.addWidget(self.open_btn)
        row.addWidget(self.clear_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.search.textChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.list.clear()
        q = self.search.text().strip().lower()
        for row_data in reversed(self._all):
            title = row_data.get("title", "")
            url = row_data.get("url", "")
            if q and q not in title.lower() and q not in url.lower():
                continue
            item = QListWidgetItem(f"{title} — {url}")
            item.setData(Qt.UserRole, row_data)
            self.list.addItem(item)


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(560, 280)

        self.homepage = QLineEdit(settings.get("homepage", homepage_url()))
        self.search_engine = QLineEdit(settings.get("search_engine", DEFAULT_SETTINGS["search_engine"]))
        self.restore_session = QCheckBox("Restore tabs from last session")
        self.restore_session.setChecked(bool(settings.get("restore_session", True)))
        self.dark_mode = QCheckBox("Use dark mode")
        self.dark_mode.setChecked(bool(settings.get("dark_mode", True)))

        form = QFormLayout()
        form.addRow("Homepage", self.homepage)
        form.addRow("Search engine", self.search_engine)
        form.addRow("", self.restore_session)
        form.addRow("", self.dark_mode)

        layout = QVBoxLayout(self)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return {
            "homepage": self.homepage.text().strip() or homepage_url(),
            "search_engine": self.search_engine.text().strip() or DEFAULT_SETTINGS["search_engine"],
            "restore_session": self.restore_session.isChecked(),
            "dark_mode": self.dark_mode.isChecked(),
        }


class DownloadsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.resize(700, 420)

        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)

    def add_download(self, label: str):
        self.list.addItem(label)


class BrowserWindow(QMainWindow):
    def __init__(self, settings_override=None, private_mode=False):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1220, 840)

        ensure_data_files()

        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        if settings_override:
            self.settings.update(settings_override)
        if not private_mode:
            self.settings["homepage"] = homepage_url()
        self.bookmarks = load_json(BOOKMARKS_FILE, [])
        self.history = load_json(HISTORY_FILE, [])
        self.closed_tabs = load_json(CLOSED_TABS_FILE, [])

        self.profile = QWebEngineProfile(self)
        if private_mode:
            self.profile.setOffTheRecord(True)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 NeonBrowser/1.0"
        )
        self.profile.downloadRequested.connect(self.handle_download)

        self.downloads_dialog = DownloadsDialog(self)
        self._build_ui()
        self.apply_theme()
        self.load_startup_tabs(private_mode=private_mode)

        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.address_bar.setFocus)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self.new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self.reopen_closed_tab)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self.open_history)
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self.toggle_bookmark_current)
        QShortcut(QKeySequence("Ctrl+J"), self, activated=self.downloads_dialog.show)

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        self.toolbar = QToolBar("Navigation")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(self.toolbar)

        style = self.style()
        self.back_btn = QAction(style.standardIcon(QStyle.SP_ArrowBack), "Back", self)
        self.forward_btn = QAction(style.standardIcon(QStyle.SP_ArrowForward), "Forward", self)
        self.reload_btn = QAction(style.standardIcon(QStyle.SP_BrowserReload), "Reload", self)
        self.home_btn = QAction(style.standardIcon(QStyle.SP_DirHomeIcon), "Home", self)
        self.new_tab_btn = QAction("+", self)
        self.bookmark_btn = QAction("☆", self)
        self.history_btn = QAction("History", self)
        self.downloads_btn = QAction("Downloads", self)
        self.private_btn = QAction("Private", self)
        self.settings_btn = QAction("Settings", self)
        self.bookmarks_menu_btn = QAction("Bookmarks", self)

        self.back_btn.triggered.connect(lambda: self._with_view(lambda v: v.back()))
        self.forward_btn.triggered.connect(lambda: self._with_view(lambda v: v.forward()))
        self.reload_btn.triggered.connect(lambda: self._with_view(lambda v: v.reload()))
        self.home_btn.triggered.connect(self.go_home)
        self.new_tab_btn.triggered.connect(self.new_tab)
        self.bookmark_btn.triggered.connect(self.toggle_bookmark_current)
        self.history_btn.triggered.connect(self.open_history)
        self.downloads_btn.triggered.connect(self.downloads_dialog.show)
        self.private_btn.triggered.connect(self.open_private_window)
        self.settings_btn.triggered.connect(self.open_settings)
        self.bookmarks_menu_btn.triggered.connect(self.open_bookmarks)

        for action in (
            self.back_btn,
            self.forward_btn,
            self.reload_btn,
            self.home_btn,
            self.new_tab_btn,
            self.bookmark_btn,
            self.bookmarks_menu_btn,
            self.history_btn,
            self.downloads_btn,
            self.private_btn,
            self.settings_btn,
        ):
            self.toolbar.addAction(action)

        self.toolbar.addSeparator()

        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Search or type a web address")
        self.address_bar.returnPressed.connect(self.navigate_to_text)
        self.toolbar.addWidget(self.address_bar)

        self.status = self.statusBar()
        self.status.showMessage("Ready")
        self.progress = QSpinBox()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(80)
        self.progress.setButtonSymbols(QSpinBox.NoButtons)
        self.status.addPermanentWidget(self.progress)

    def _with_view(self, func):
        view = self.current_view()
        if view:
            func(view)

    def apply_theme(self):
        dark = bool(self.settings.get("dark_mode", True))
        if dark:
            self.setStyleSheet(
                """
                QMainWindow, QDialog { background: #121212; color: #ececec; }
                QToolBar { background: #181818; border: none; spacing: 6px; padding: 6px; }
                QLineEdit, QListWidget, QTreeWidget, QSpinBox {
                    background: #1b1b1b; color: #f1f1f1; border: 1px solid #333;
                    border-radius: 10px; padding: 8px;
                }
                QTabWidget::pane { border: none; }
                QTabBar::tab {
                    background: #1c1c1c; color: #d9d9d9; padding: 10px 14px;
                    border-top-left-radius: 10px; border-top-right-radius: 10px;
                    margin-right: 4px;
                }
                QTabBar::tab:selected { background: #2a2a2a; color: white; }
                QPushButton, QToolButton {
                    background: #232323; color: #f0f0f0; border: 1px solid #333;
                    padding: 8px 12px; border-radius: 10px;
                }
                QPushButton:hover, QToolButton:hover { background: #2d2d2d; }
                QStatusBar { background: #181818; color: #eee; }
                """
            )
        else:
            self.setStyleSheet("")

    def current_view(self):
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def new_tab(self, url=None, title="New Tab", foreground=True):
        page = BrowserPage(self.profile, self)
        view = QWebEngineView(self)
        view.setPage(page)
        view.setZoomFactor(1.0)

        def on_title(text):
            index = self.tabs.indexOf(view)
            if index != -1:
                self.tabs.setTabText(index, (text or "New Tab")[:24])
            self.setWindowTitle(f"{text} - {APP_NAME}" if text else APP_NAME)
            self.record_page(view)

        def on_url(qurl):
            if view is self.current_view():
                self.address_bar.setText(qurl.toString())
            self.update_bookmark_button()
            self.record_page(view)

        def on_progress(value):
            self.progress.setValue(value)

        def on_load_started():
            self.progress.setValue(0)

        def on_load_finished(ok):
            self.progress.setValue(100 if ok else 0)
            self.record_page(view)

        view.titleChanged.connect(on_title)
        view.urlChanged.connect(on_url)
        view.loadStarted.connect(on_load_started)
        view.loadProgress.connect(on_progress)
        view.loadFinished.connect(on_load_finished)

        index = self.tabs.addTab(view, title)
        if foreground:
            self.tabs.setCurrentIndex(index)

        if url is not None:
            view.setUrl(url)

        return view

    def add_tab(self, url: QUrl, foreground=True):
        return self.new_tab(url=url, foreground=foreground)

    def load_startup_tabs(self, private_mode=False):
        if private_mode:
            self.new_tab(QUrl("about:blank"))
            return

        if self.settings.get("restore_session", True):
            session = load_json(SESSION_FILE, [])
            if session:
                for entry in session:
                    self.new_tab(QUrl(entry.get("url", self.settings.get("homepage", homepage_url()))), foreground=False)
                self.tabs.setCurrentIndex(0)
                return

        self.new_tab(QUrl(self.settings.get("homepage", homepage_url())))

    def save_session(self):
        session = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, QWebEngineView):
                session.append({"title": w.title(), "url": w.url().toString()})
        save_json(SESSION_FILE, session)

    def current_tab_changed(self, index):
        view = self.tabs.widget(index)
        if isinstance(view, QWebEngineView):
            self.address_bar.setText(view.url().toString())
            self.address_bar.setCursorPosition(0)
            self.update_bookmark_button()

    def close_tab(self, index):
        view = self.tabs.widget(index)
        if isinstance(view, QWebEngineView):
            self.closed_tabs.append(
                {"title": view.title() or "Untitled", "url": view.url().toString(), "closed_at": now_iso()}
            )
            save_json(CLOSED_TABS_FILE, self.closed_tabs[-50:])
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.new_tab(QUrl(self.settings.get("homepage", homepage_url())))

    def close_current_tab(self):
        if self.tabs.count() > 0:
            self.close_tab(self.tabs.currentIndex())

    def navigate_to_text(self):
        text = self.address_bar.text()
        url = smart_url_or_search(text, self.settings.get("search_engine", DEFAULT_SETTINGS["search_engine"]))
        self._with_view(lambda v: v.setUrl(url))

    def go_home(self):
        self._with_view(lambda v: v.setUrl(QUrl(self.settings.get("homepage", homepage_url()))))

    def record_page(self, view):
        if not isinstance(view, QWebEngineView):
            return
        url = view.url().toString()
        if not url or url.startswith("about:"):
            return
        title = view.title().strip() or url
        if not self.history or self.history[-1].get("url") != url:
            self.history.append({"title": title, "url": url, "visited_at": now_iso()})
            self.history = self.history[-1000:]
            save_json(HISTORY_FILE, self.history)

    def update_bookmark_button(self):
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        self.bookmark_btn.setText("★" if any(b.get("url") == url for b in self.bookmarks) else "☆")

    def toggle_bookmark_current(self):
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        title = view.title() or url
        existing = next((b for b in self.bookmarks if b.get("url") == url), None)
        if existing:
            self.bookmarks = [b for b in self.bookmarks if b.get("url") != url]
        else:
            self.bookmarks.append({"title": title, "url": url, "added_at": now_iso()})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self.update_bookmark_button()

    def open_history(self):
        dlg = HistoryDialog(self.history, self)
        dlg.open_btn.clicked.connect(lambda: self.open_selected_history(dlg))
        dlg.clear_btn.clicked.connect(lambda: self.clear_history(dlg))
        dlg.exec()

    def open_selected_history(self, dlg):
        item = dlg.list.currentItem()
        if not item:
            return
        row = item.data(Qt.UserRole)
        if row and self.current_view():
            self.current_view().setUrl(QUrl(row.get("url", "")))
            dlg.accept()

    def clear_history(self, dlg):
        if QMessageBox.question(self, "Clear history", "Delete all browsing history?") != QMessageBox.Yes:
            return
        self.history = []
        save_json(HISTORY_FILE, self.history)
        dlg.refresh()

    def open_bookmarks(self):
        dlg = BookmarkDialog(self.bookmarks, self)
        dlg.open_btn.clicked.connect(lambda: self.open_selected_bookmark(dlg))
        dlg.remove_btn.clicked.connect(lambda: self.remove_selected_bookmark(dlg))
        dlg.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.get_selected_bookmark_url(dlg) or ""))
        dlg.exec()

    def get_selected_bookmark_url(self, dlg):
        item = dlg.tree.currentItem()
        if not item:
            return None
        bm = item.data(0, Qt.UserRole)
        return bm.get("url") if bm else None

    def open_selected_bookmark(self, dlg):
        url = self.get_selected_bookmark_url(dlg)
        if url and self.current_view():
            self.current_view().setUrl(QUrl(url))
            dlg.accept()

    def remove_selected_bookmark(self, dlg):
        item = dlg.tree.currentItem()
        if not item:
            return
        bm = item.data(0, Qt.UserRole)
        if not bm:
            return
        self.bookmarks = [b for b in self.bookmarks if b.get("url") != bm.get("url")]
        save_json(BOOKMARKS_FILE, self.bookmarks)
        dlg.refresh()

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == QDialog.Accepted:
            self.settings.update(dlg.values())
            self.settings["homepage"] = homepage_url()
            save_json(SETTINGS_FILE, self.settings)
            self.apply_theme()

    def handle_download(self, item: QWebEngineDownloadRequest):
        suggested = item.downloadFileName() or "download"
        target, _ = QFileDialog.getSaveFileName(self, "Save file", str(Path.home() / suggested))
        if not target:
            item.cancel()
            return
        item.setDownloadDirectory(str(Path(target).parent))
        item.setDownloadFileName(Path(target).name)
        item.accept()
        self.downloads_dialog.add_download(f"Downloading: {Path(target).name}")

    def open_private_window(self):
        self.private_window = BrowserWindow(settings_override={**self.settings, "homepage": "about:blank"}, private_mode=True)
        self.private_window.setWindowTitle("Private Window - Neon Browser")
        self.private_window.show()

    def reopen_closed_tab(self):
        if not self.closed_tabs:
            return
        entry = self.closed_tabs.pop()
        save_json(CLOSED_TABS_FILE, self.closed_tabs)
        self.new_tab(QUrl(entry.get("url", self.settings.get("homepage", homepage_url()))))

    def closeEvent(self, event):
        self.save_session()
        save_json(SETTINGS_FILE, self.settings)
        save_json(BOOKMARKS_FILE, self.bookmarks)
        save_json(HISTORY_FILE, self.history)
        super().closeEvent(event)


def main():
    ensure_data_files()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    window = BrowserWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
