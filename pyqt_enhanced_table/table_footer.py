"""
Table Footer Component.
Statistics, page size selector, and pagination controls.
"""

from typing import Dict
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta

from .theme import COLORS, ICONS


class MiniStat(QFrame):
    """Small statistic card"""

    def __init__(
        self,
        title: str,
        icon: str = None,
        color: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setProperty("class", "mini-stat")
        self.setFixedHeight(32)

        # Style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet(
            f"""
            MiniStat {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['bg_hover']};
                border-radius: 4px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            .mini-stat-title {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
                font-weight: 500;
            }}
            .mini-stat-value {{
                color: {COLORS['text_primary']};
                font-size: 12px;
                font-weight: bold;
            }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 8, 0)
        layout.setSpacing(6)

        # Icon
        if icon:
            icon_color = color or COLORS.get("primary", "#3498db")
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon, color=icon_color).pixmap(14, 14))
            layout.addWidget(icon_label)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "mini-stat-title")
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel("0")
        self.value_label.setProperty("class", "mini-stat-value")
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(str(value))


class TableFooter(QWidget):
    """
    Table Footer Component.
    Left: Mini stats
    Center: Page size selector
    Right: Pagination controls
    """

    # Signals
    page_size_changed = pyqtSignal(int)
    next_page_clicked = pyqtSignal()
    prev_page_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats: Dict[str, MiniStat] = {}
        self._current_page = 1
        self._total_pages = 1
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        self.setProperty("class", "table-footer")

        # General Footer Style
        self.setStyleSheet(
            f"""
            .table-footer {{
                background-color: {COLORS['bg_primary']};
                border-top: 1px solid #333333;
            }}
            .footer-label, .pagination-label {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
            }}
            QComboBox {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: {COLORS['text_secondary']};
                padding: 0px;
                padding-left: 4px;
                width: 45px;
                min-width: 45px;
                max-width: 45px;
                height: 24px;
                min-height: 24px;
                max-height: 24px;
            }}
            QComboBox:hover {{
                background-color: {COLORS['bg_hover']};
                border: 1px solid {COLORS['active_border'] if 'active_border' in COLORS else '#505050'};
                color: {COLORS['text_primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 14px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #909090;
                margin-right: 4px;
            }}
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border: 1px solid {COLORS['active_border'] if 'active_border' in COLORS else '#505050'};
            }}
            QPushButton:disabled {{
                opacity: 0.3;
            }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # LEFT: Stats Container
        self._stats_container = QHBoxLayout()
        self._stats_container.setSpacing(8)
        layout.addLayout(self._stats_container)

        # Spacer
        layout.addStretch()

        # RIGHT: Controls (in a frame)
        self._controls_frame = QFrame()
        self._controls_frame.setProperty("class", "footer-controls")
        self._controls_frame.setFixedHeight(32)

        self._controls_frame.setStyleSheet(
            f"""
            .footer-controls {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['bg_hover']};
                border-radius: 4px;
            }}
        """
        )

        controls_layout = QHBoxLayout(self._controls_frame)
        controls_layout.setContentsMargins(4, 0, 4, 0)
        controls_layout.setSpacing(8)

        # Page Size Selector
        self._page_size_combo = QComboBox()
        self._page_size_combo.addItems(["10", "25", "50", "100"])
        self._page_size_combo.setCurrentText("25")
        self._page_size_combo.setFixedWidth(50)
        self._page_size_combo.setFixedHeight(24)
        self._page_size_combo.setToolTip("Records per page")
        self._page_size_combo.currentTextChanged.connect(
            lambda v: self.page_size_changed.emit(int(v))
        )
        controls_layout.addWidget(self._page_size_combo)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(
            f"background-color: {COLORS['bg_hover']}; border: none; width: 1px;"
        )
        line.setFixedHeight(16)
        controls_layout.addWidget(line)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(2)

        self._prev_btn = QPushButton()
        self._prev_btn.setIcon(
            qta.icon(ICONS["arrow_left"], color=COLORS["text_secondary"])
        )
        self._prev_btn.setFixedSize(24, 24)
        self._prev_btn.setProperty("class", "pagination-btn")
        self._prev_btn.clicked.connect(self.prev_page_clicked.emit)
        pagination_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("1/1")
        self._page_label.setProperty("class", "pagination-label")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setMinimumWidth(30)
        pagination_layout.addWidget(self._page_label)

        self._next_btn = QPushButton()
        self._next_btn.setIcon(
            qta.icon(ICONS["arrow_right"], color=COLORS["text_secondary"])
        )
        self._next_btn.setFixedSize(24, 24)
        self._next_btn.setProperty("class", "pagination-btn")
        self._next_btn.clicked.connect(self.next_page_clicked.emit)
        pagination_layout.addWidget(self._next_btn)

        controls_layout.addLayout(pagination_layout)

        layout.addWidget(self._controls_frame)

    def add_stat(
        self,
        key: str,
        title: str,
        icon: str = None,
        color: str = None,
    ):
        """Add stat card"""
        stat = MiniStat(title, icon, color, self)
        self._stats[key] = stat
        self._stats_container.addWidget(stat)

    def update_stat(self, key: str, value):
        """Update stat value"""
        if key in self._stats:
            self._stats[key].set_value(value)

    def update_stats(self, stats: dict):
        """Update multiple stats"""
        for key, value in stats.items():
            self.update_stat(key, value)

    def update_pagination(
        self,
        current: int,
        total_pages: int,
        total_records: int = None,
    ):
        """Update pagination info"""
        self._current_page = current
        self._total_pages = total_pages

        self._page_label.setText(f"{current} / {total_pages}")
        self._prev_btn.setEnabled(current > 1)
        self._next_btn.setEnabled(current < total_pages)

    def set_page_size(self, size: int):
        """Set page size"""
        self._page_size_combo.setCurrentText(str(size))

    def get_page_size(self) -> int:
        """Get current page size"""
        return int(self._page_size_combo.currentText())
