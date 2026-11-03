"""Modern desktop GUI for SlipSurfaceIQ Correlation.

Contemporary card-based interface (soft shadows, accent colors, clean typography)
inspired by recent design trends. Uses PySide6.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QScrollArea, QFormLayout, QGroupBox, QLabel, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QSplitter,
    QStatusBar, QFrame, QStackedWidget,
)

from slipsurface.correlation.forms import schema, defaults, to_config, from_config, project_file
from slipsurface.correlation.engine import analyse
from slipsurface.correlation import APP_NAME, __version__

# Modern palette
BG = "#f7f8fa"
CARD = "#ffffff"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
TEXT = "#111827"
MUTED = "#6b7280"
BORDER = "#e5e7eb"


def modern_palette() -> QPalette:
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor(CARD))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.Button, QColor(CARD))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    return pal


MODERN_STYLE = f"""
QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; font-family: 'Segoe UI', system-ui, sans-serif; }}
QGroupBox {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    margin-top: 12px;
    padding: 16px;
    font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {MUTED}; }}
QPushButton {{
    background: {ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:disabled {{ background: #9ca3af; }}
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    background: white;
}}
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{
    background: transparent;
    padding: 10px 16px;
    margin-right: 4px;
    border-radius: 8px;
    color: {MUTED};
}}
QTabBar::tab:selected {{ background: {CARD}; color: {ACCENT}; font-weight: 600; }}
QTextEdit {{ border: 1px solid {BORDER}; border-radius: 12px; background: {CARD}; padding: 8px; }}
QStatusBar {{ background: {CARD}; border-top: 1px solid {BORDER}; }}
"""


class CorrelationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  {__version__}")
        self.resize(1280, 840)
        self.lang = "en"
        self.values = defaults(self.lang)
        self.fields: dict = {}
        self.tables: dict = {}

        self.setStyleSheet(MODERN_STYLE)
        self._build_ui()
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready — enter data and analyse")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("SlipSurfaceIQ  Correlation")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #111827;")
        subtitle = QLabel("SPT · CPT · Lab correlations")
        subtitle.setStyleSheet(f"color: {MUTED}; font-size: 13px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(subtitle)
        root.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # Left inputs
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 8, 0)
        self.input_tabs = QTabWidget()
        left_lay.addWidget(self.input_tabs)
        self._build_input_tabs()
        btn_row = QHBoxLayout()
        self.btn_analyse = QPushButton("Analyse")
        self.btn_analyse.clicked.connect(self.run_analysis)
        self.btn_save = QPushButton("Save Project")
        self.btn_save.setStyleSheet(f"background: white; color: {ACCENT}; border: 1px solid {BORDER};")
        self.btn_save.clicked.connect(self.save_project)
        btn_row.addWidget(self.btn_analyse)
        btn_row.addWidget(self.btn_save)
        btn_row.addStretch()
        left_lay.addLayout(btn_row)
        splitter.addWidget(left)

        # Right results
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setPlaceholderText("Results will appear here…")
        splitter.addWidget(self.results)
        splitter.setSizes([520, 700])

        self._build_menu()

    def _build_menu(self):
        menu = self.menuBar()
        file_m = menu.addMenu("&File")
        file_m.addAction("Open…", self.open_project)
        file_m.addAction("Save…", self.save_project)
        file_m.addSeparator()
        file_m.addAction("Quit", self.close)
        lang_m = menu.addMenu("&Language")
        lang_m.addAction("English", lambda: self.set_language("en"))
        lang_m.addAction("Türkçe", lambda: self.set_language("tr"))

    def set_language(self, lang: str):
        self.lang = lang
        while self.input_tabs.count():
            self.input_tabs.removeTab(0)
        self.fields.clear()
        self.tables.clear()
        self.values = defaults(lang)
        self._build_input_tabs()
        self.status.showMessage(f"Language: {lang}")

    def _build_input_tabs(self):
        sch = schema(self.lang)
        # Soil + tests as tables
        for key in ("soil_profile", "spt_tests", "cpt_tests", "vs_tests"):
            if key in sch:
                self._add_table_tab(key, sch[key])
        # Other groups
        for part in sch:
            if part not in ("soil_profile", "spt_tests", "cpt_tests", "vs_tests") and isinstance(sch[part], dict) and "groups" in sch[part]:
                self._add_groups_tab(part, sch[part])

    def _add_table_tab(self, name: str, spec: dict):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        lay = QVBoxLayout(w)
        if spec.get("note"):
            note = QLabel(spec["note"])
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {MUTED};")
            lay.addWidget(note)
        table = QTableWidget()
        cols = spec.get("columns", [])
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels([c.get("label", c["key"]) for c in cols])
        rows = spec.get("rows", [])
        table.setRowCount(max(len(rows), 3))
        for r, row in enumerate(rows):
            for c, col in enumerate(cols):
                table.setItem(r, c, QTableWidgetItem(str(row.get(col["key"], ""))))
        lay.addWidget(table)
        add = QPushButton("+ Add row")
        add.setStyleSheet(f"background: white; color: {ACCENT}; border: 1px solid {BORDER};")
        add.clicked.connect(lambda: table.insertRow(table.rowCount()))
        lay.addWidget(add)
        scroll.setWidget(w)
        self.tables[name] = table
        self.input_tabs.addTab(scroll, name.replace("_", " ").title())

    def _add_groups_tab(self, name: str, part: dict):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        lay = QVBoxLayout(w)
        for group in part.get("groups", []):
            gb = QGroupBox(group.get("title", name))
            form = QFormLayout(gb)
            for field in group.get("fields", []):
                widget = self._make_field(field)
                form.addRow(field.get("label", field["key"]), widget)
                self.fields[field["key"]] = widget
            lay.addWidget(gb)
        lay.addStretch()
        scroll.setWidget(w)
        self.input_tabs.addTab(scroll, name.capitalize())

    def _make_field(self, field: dict):
        kind = field.get("kind", "number")
        default = field.get("default")
        if kind == "select":
            cb = QComboBox()
            for opt in field.get("options", []):
                cb.addItem(str(opt.get("label", opt.get("value", ""))), opt.get("value"))
            idx = cb.findData(default)
            if idx >= 0:
                cb.setCurrentIndex(idx)
            return cb
        if kind == "check":
            chk = QCheckBox()
            chk.setChecked(bool(default))
            return chk
        if kind in ("number", "float"):
            sp = QDoubleSpinBox()
            sp.setDecimals(field.get("dec", 2))
            sp.setRange(field.get("lo", -1e9), field.get("hi", 1e9))
            sp.setValue(float(default or 0))
            return sp
        return QLineEdit(str(default or ""))

    def _collect_values(self) -> dict:
        vals = dict(self.values)
        for key, widget in self.fields.items():
            if isinstance(widget, QComboBox):
                vals[key] = widget.currentData()
            elif isinstance(widget, QCheckBox):
                vals[key] = widget.isChecked()
            elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                vals[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                vals[key] = widget.text()
        for name, table in self.tables.items():
            sch = schema(self.lang).get(name, {})
            cols = sch.get("columns", [])
            rows = []
            for r in range(table.rowCount()):
                row = {}
                has = False
                for c, col in enumerate(cols):
                    item = table.item(r, c)
                    text = (item.text() if item else "").strip()
                    key = col["key"]
                    kind = col.get("kind", "text")
                    if kind == "number":
                        try:
                            row[key] = float(text) if text else 0.0
                        except ValueError:
                            row[key] = 0.0
                    else:
                        row[key] = text
                    if text:
                        has = True
                if has:
                    rows.append(row)
            vals[name] = rows
        return vals

    def run_analysis(self):
        try:
            vals = self._collect_values()
            cfg = to_config(vals)
            result = analyse(cfg)
            self.last_result = result
            text = json.dumps(vars(result) if hasattr(result, "__dict__") else result,
                              indent=2, default=str, ensure_ascii=False)[:12000]
            self.results.setPlainText(text)
            self.status.showMessage("Analysis complete")
        except Exception as e:
            QMessageBox.critical(self, "Analysis error", f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}")

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.values = from_config(data["config"]) if isinstance(data, dict) and "config" in data else data
            self.set_language(self.lang)
            self.status.showMessage(f"Opened {path}")
        except Exception as e:
            QMessageBox.critical(self, "Open error", str(e))

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save", "project.correlation.json", "JSON (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(project_file(self._collect_values()), indent=2, ensure_ascii=False), encoding="utf-8")
            self.status.showMessage(f"Saved {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))


def run(argv=None) -> int:
    app = QApplication.instance() or QApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setPalette(modern_palette())
    win = CorrelationWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
