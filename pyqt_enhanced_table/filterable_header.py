"""
Excel-like filterable QHeaderView.
"""

from typing import Dict, Optional
from PyQt6.QtWidgets import QHeaderView, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent
import qtawesome as qta

from .theme import COLORS, FONT_FAMILY_QT, ICONS


class FilterableHeaderView(QHeaderView):
    """
    Excel-like filterable table header.

    In each column:
    - Column Title
    - Filter Icon (▼)
    - Active Filter Indicator (dot)

    Clicks:
    - Left Click on Section: Sort
    - Click on Filter Icon: Open FilterPopup
    """

    # Signals
    filter_icon_clicked = pyqtSignal(int, QPoint)  # section_idx, global_pos
    filter_cleared = pyqtSignal(int)  # section_idx

    # Metrics
    FILTER_ICON_WIDTH = 20
    FILTER_ICON_MARGIN = 4

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(orientation, parent)

        # Filter state
        self._filterable_columns: Dict[int, bool] = {}  # section_idx -> filterable
        self._active_filters: Dict[int, bool] = {}  # section_idx -> has_active_filter

        # Hover state
        self._hover_section = -1
        self._hover_on_filter_icon = False

        # Mouse tracking needed for hover effects
        self.setMouseTracking(True)

        # Style
        self.setHighlightSections(False)
        self.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # Sorting
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)

    def set_column_filterable(self, section: int, filterable: bool):
        """Set whether a column shows the filter icon"""
        self._filterable_columns[section] = filterable

    def set_filter_active(self, section: int, active: bool):
        """Set indicator for active filter on a column"""
        self._active_filters[section] = active
        self.updateSection(section)

    def is_filter_active(self, section: int) -> bool:
        """Check if filter is active"""
        return self._active_filters.get(section, False)

    def is_column_filterable(self, section: int) -> bool:
        """Check if column is filterable"""
        return self._filterable_columns.get(section, True)

    def clear_all_filter_indicators(self):
        """Clear all filter indicators"""
        self._active_filters.clear()
        self.viewport().update()

    def _get_filter_icon_rect(self, rect: QRect) -> QRect:
        """Calculate filter icon rect within the section rect"""
        # Icon on the right
        icon_rect = QRect(
            rect.right() - self.FILTER_ICON_WIDTH - self.FILTER_ICON_MARGIN,
            rect.top(),
            self.FILTER_ICON_WIDTH,
            rect.height(),
        )
        return icon_rect

    def _get_filter_icon_rect_for_section(self, section: int) -> QRect:
        """Calculate filter icon rect for a specific section index"""
        if section < 0 or section >= self.count():
            return QRect()

        # Viewport position
        x = self.sectionViewportPosition(section)
        width = self.sectionSize(section)
        height = self.height()

        section_rect = QRect(x, 0, width, height)
        return self._get_filter_icon_rect(section_rect)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        """Paint header section"""
        painter.save()

        # Background
        is_hover = logicalIndex == self._hover_section
        bg_color = COLORS["bg_hover"] if is_hover else COLORS["bg_secondary"]
        painter.fillRect(rect, QColor(bg_color))

        # Bottom Border
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        # Right Border (Separator)
        painter.drawLine(rect.topRight(), rect.bottomRight())

        # Text
        text = self.model().headerData(
            logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        if text:
            painter.setPen(QColor(COLORS["text_primary"]))
            font = QFont(FONT_FAMILY_QT, 11)
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)

            # Adjust text rect to avoid overlap with filter icon
            text_rect = rect.adjusted(
                8,
                0,
                (
                    -self.FILTER_ICON_WIDTH - self.FILTER_ICON_MARGIN * 2
                    if self.is_column_filterable(logicalIndex)
                    else -8
                ),
                0,
            )
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(text),
            )

        # Sort Indicator - Left of filter icon
        sort_indicator = self.sortIndicatorSection()
        if sort_indicator == logicalIndex:
            sort_order = self.sortIndicatorOrder()
            # Use icons from theme
            icon_name = (
                ICONS["sort_up"]
                if sort_order == Qt.SortOrder.AscendingOrder
                else ICONS["sort_down"]
            )
            icon = qta.icon(icon_name, color=COLORS["primary"])

            icon_size = 16
            icon_x = rect.right() - self.FILTER_ICON_WIDTH - icon_size - 8
            icon_y = rect.top() + (rect.height() - icon_size) // 2
            icon.paint(painter, QRect(icon_x, icon_y, icon_size, icon_size))

        # Filter Icon
        is_filterable = self.is_column_filterable(logicalIndex)
        if is_filterable:
            self._draw_filter_icon(painter, rect, logicalIndex)

        painter.restore()

    def _draw_filter_icon(self, painter: QPainter, rect: QRect, section: int):
        """Draw the filter icon"""
        icon_rect = self._get_filter_icon_rect(rect)

        # Hover background
        is_icon_hover = section == self._hover_section and self._hover_on_filter_icon
        if is_icon_hover:
            painter.fillRect(
                icon_rect.adjusted(2, 4, -2, -4), QColor(COLORS["bg_active"])
            )

        # Filter Icon Symbol (▼) or Generic Icon
        painter.setPen(QColor(COLORS["text_secondary"]))
        font = QFont(FONT_FAMILY_QT, 9)
        painter.setFont(font)
        painter.drawText(
            icon_rect,
            Qt.AlignmentFlag.AlignCenter,
            "▼",
        )

        # Active Filter Indicator (Dot)
        if self.is_filter_active(section):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["primary"]))
            # Small circle
            center = icon_rect.center()
            painter.drawEllipse(center.x() + 5, center.y() - 6, 6, 6)

    def _get_section_at(self, pos: QPoint) -> int:
        """Get logical index at position manually"""
        for logical_idx in range(self.count()):
            if self.isSectionHidden(logical_idx):
                continue

            x = self.sectionViewportPosition(logical_idx)
            w = self.sectionSize(logical_idx)

            if x <= pos.x() < x + w:
                return logical_idx
        return -1

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for hover effects"""
        pos = event.position().toPoint()
        section = self._get_section_at(pos)

        old_hover = self._hover_section
        old_icon_hover = self._hover_on_filter_icon

        self._hover_section = section

        # Check if hovering over filter icon
        if section >= 0 and self.is_column_filterable(section):
            icon_rect = self._get_filter_icon_rect_for_section(section)
            self._hover_on_filter_icon = icon_rect.contains(pos)
        else:
            self._hover_on_filter_icon = False

        # Redraw if changed
        if (
            old_hover != self._hover_section
            or old_icon_hover != self._hover_on_filter_icon
        ):
            self.viewport().update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint()
        section = self._get_section_at(pos)

        if section >= 0 and self.is_column_filterable(section):
            icon_rect = self._get_filter_icon_rect_for_section(section)
            if icon_rect.contains(pos):
                # Clicked on filter icon
                global_pos = self.mapToGlobal(icon_rect.bottomLeft())
                self.filter_icon_clicked.emit(section, global_pos)
                return

        # Normal click (sorting)
        super().mousePressEvent(event)

    def leaveEvent(self, event):
        """Reset hover state on leave"""
        self._hover_section = -1
        self._hover_on_filter_icon = False
        self.viewport().update()
        super().leaveEvent(event)

    def sizeHint(self):
        """Recommended size"""
        hint = super().sizeHint()
        hint.setHeight(36)
        return hint
