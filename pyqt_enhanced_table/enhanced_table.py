"""
Enhanced Table Component
Features: Filtering, Sorting, Column Management, Persistent Settings
"""

from typing import List, Dict, Optional, Set, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
    QAbstractItemView,
    QWidget,
    QHBoxLayout,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSettings
from PyQt6.QtGui import QAction, QKeySequence

from .filterable_header import FilterableHeaderView
from .filter_popup import FilterPopup

if TYPE_CHECKING:
    from .active_filters_bar import ActiveFiltersBar


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom item for numeric sorting"""

    def __init__(self, value, display_text=None):
        text = display_text if display_text is not None else str(value)
        super().__init__(text)
        self.numeric_value = value

    def __lt__(self, other):
        """Sort operator (<)"""
        if hasattr(other, "numeric_value"):
            return self.numeric_value < other.numeric_value

        # Fallback to text sort
        try:
            # Check for empty strings
            if not self.text() and other.text():
                return True  # Empty < Full
            if self.text() and not other.text():
                return False

            return super().__lt__(other)
        except Exception:
            return super().__lt__(other)


class ColumnConfig:
    """Column Configuration Class"""

    def __init__(
        self,
        key: str,
        title: str,
        width: int = 100,
        stretch: bool = False,
        visible: bool = True,
        filterable: bool = True,
        filter_type: str = "text",
        resizable: bool = True,
        movable: bool = True,
        hideable: bool = True,
        sortable: bool = True,
        align: Optional[Qt.AlignmentFlag] = None,
    ):
        self.key = key
        self.title = title
        self.width = width
        self.stretch = stretch
        self.visible = visible
        self.filterable = filterable
        self.filter_type = filter_type
        self.resizable = resizable
        self.movable = movable
        self.hideable = hideable
        self.sortable = sortable
        self.align = align


class EnhancedTableWidget(QTableWidget):
    """
    Enhanced Table Widget with advanced features.
    """

    # Signals
    row_double_clicked = pyqtSignal(int)  # Row ID
    row_selected = pyqtSignal(int)  # Row ID
    settings_changed = pyqtSignal()  # When settings change
    filter_changed = pyqtSignal(dict)  # When active filters change
    rows_filtered = pyqtSignal(int, int)  # Post-filter (visible, total)

    def __init__(
        self,
        table_id: str,
        columns: List[ColumnConfig],
        user_id: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.table_id = table_id
        self.user_id = user_id
        self.columns = {col.key: col for col in columns}
        self.column_order = [col.key for col in columns]

        # Filtering
        self._active_filters: Dict[str, dict] = {}
        self._predefined_options: Dict[str, List[str]] = {}
        self._filter_popup: Optional[FilterPopup] = None

        # CSS class
        self.setProperty("class", "enhanced-table")

        self._load_settings()
        self._setup_table()
        self._setup_filterable_header()
        self._apply_column_settings()
        self._connect_signals()
        self._load_filter_settings()

    def set_filter_options(self, column_key: str, options: List[str]):
        """Set predefined options for filter menu"""
        self._predefined_options[column_key] = options

    def get_logical_visible_columns(self) -> List[str]:
        """Get visible columns in logical (original) order"""
        return [key for key in self.column_order if self.columns[key].visible]

    def _get_table_index(self, column_key: str) -> int:
        """Get logical index of column in table"""
        try:
            return self.column_order.index(column_key)
        except ValueError:
            return -1

    def _setup_table(self):
        """Basic table setup"""
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setDefaultSectionSize(36)
        self.setShowGrid(False)
        self.setSortingEnabled(False)  # Using custom handler

        # Create columns (all logical columns)
        self.setColumnCount(len(self.column_order))
        self.setHorizontalHeaderLabels(
            [self.columns[key].title for key in self.column_order]
        )

        # Hide initially hidden columns
        for i, key in enumerate(self.column_order):
            if not self.columns[key].visible:
                self.setColumnHidden(i, True)

    def _setup_filterable_header(self):
        """Setup filterable header"""
        self._filter_header = FilterableHeaderView(Qt.Orientation.Horizontal, self)
        self.setHorizontalHeader(self._filter_header)

        self._filter_header.setSectionsMovable(True)
        self._filter_header.setStretchLastSection(False)
        self._filter_header.sectionMoved.connect(self._on_section_moved)
        self._filter_header.sectionResized.connect(self._on_section_resized)
        self._filter_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._filter_header.customContextMenuRequested.connect(self._show_column_menu)

        # Filter signal
        self._filter_header.filter_icon_clicked.connect(self._on_filter_icon_clicked)

        # Set titles
        self.setHorizontalHeaderLabels(
            [self.columns[k].title for k in self.column_order]
        )

        # Set filterability
        for logical_idx, key in enumerate(self.column_order):
            col = self.columns[key]
            self._filter_header.set_column_filterable(logical_idx, col.filterable)

    def _connect_signals(self):
        """Connect internal signals"""
        self.doubleClicked.connect(self._on_double_click)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self._filter_header.sectionClicked.connect(self._on_header_clicked)

    def keyPressEvent(self, event):
        """Copy shortcut (Ctrl+C)"""
        if event.matches(QKeySequence.StandardKey.Copy):
            self._copy_selection()
        else:
            super().keyPressEvent(event)

    def _copy_selection(self):
        """Copy selected cells to clipboard as TSV"""
        selection = self.selectedIndexes()
        if not selection:
            return

        rows = sorted(list(set(index.row() for index in selection)))
        columns = sorted(list(set(index.column() for index in selection)))

        row_map = {r: i for i, r in enumerate(rows)}
        col_map = {c: i for i, c in enumerate(columns)}

        data = [["" for _ in columns] for _ in rows]

        for index in selection:
            r = row_map[index.row()]
            c = col_map[index.column()]
            val = index.data(Qt.ItemDataRole.DisplayRole)
            data[r][c] = str(val) if val is not None else ""

        tsv = "\n".join(["\t".join(row) for row in data])
        QApplication.clipboard().setText(tsv)

    def _on_header_clicked(self, logical_index: int):
        """Sort when header is clicked"""
        header = self.horizontalHeader()
        current_order = header.sortIndicatorOrder()

        self.setSortingEnabled(True)
        self.sortItems(logical_index, current_order)
        self.setSortingEnabled(False)

    def _on_filter_icon_clicked(self, section: int, global_pos: QPoint):
        """Show filter popup"""
        if section < 0 or section >= len(self.column_order):
            return

        column_key = self.column_order[section]
        col_config = self.columns[column_key]

        unique_values = self.get_unique_values(column_key)
        current_filter = self._active_filters.get(column_key)

        self._filter_popup = FilterPopup(
            column_key=column_key,
            column_title=col_config.title,
            unique_values=unique_values,
            current_filter=current_filter,
            parent=self,
        )
        self._filter_popup.filter_applied.connect(self._on_filter_applied)
        self._filter_popup.filter_cleared.connect(
            lambda: self._on_filter_cleared(column_key)
        )

        self._filter_popup.move(global_pos)

        # Boundary check
        screen = self.screen()
        if screen:
            screen_width = screen.geometry().width()
            popup_width = self._filter_popup.width()
            if global_pos.x() + popup_width > screen_width:
                new_x = global_pos.x() - popup_width + 20
                self._filter_popup.move(new_x, global_pos.y())

        self._filter_popup.show()

    def _on_filter_applied(self, filter_data: dict):
        """Filter applied callback"""
        column_key = filter_data.get("column_key")
        if not column_key:
            return

        if filter_data.get("all_selected") and "text_filter" not in filter_data:
            self._on_filter_cleared(column_key)
            return

        self._active_filters[column_key] = filter_data

        visible_columns = self.get_visible_columns()
        if column_key in visible_columns:
            section = visible_columns.index(column_key)
            self._filter_header.set_filter_active(section, True)

        self._apply_filters()
        self._save_filter_settings()
        self.filter_changed.emit(self._active_filters)

    def _on_filter_cleared(self, column_key: str):
        """Filter cleared callback"""
        if column_key in self._active_filters:
            del self._active_filters[column_key]

        visible_columns = self.get_visible_columns()
        if column_key in visible_columns:
            section = visible_columns.index(column_key)
            self._filter_header.set_filter_active(section, False)

        self._apply_filters()
        self._save_filter_settings()
        self.filter_changed.emit(self._active_filters)

    def _apply_filters(self):
        """Apply all active filters"""
        if getattr(self, "server_side_mode", False):
            self.rows_filtered.emit(self.rowCount(), self.rowCount())
            return

        visible_count = 0
        for row in range(self.rowCount()):
            visible = True
            for col_key, filter_data in self._active_filters.items():
                if col_key not in self.columns:
                    continue

                col_idx = self._get_table_index(col_key)
                if col_idx == -1:
                    continue

                item = self.item(row, col_idx)
                cell_text = item.text() if item else ""

                all_sel = filter_data.get("all_selected", True)
                if isinstance(all_sel, str):
                    all_sel = all_sel.lower() == "true"

                if not all_sel:
                    allowed = filter_data.get("selected_values", [])
                    match = False
                    for val in allowed:
                        if str(val) == cell_text:
                            match = True
                            break
                    if not match:
                        visible = False
                        break

                text_filter = filter_data.get("text_filter")
                if text_filter:
                    mode = text_filter.get("mode", "contains")
                    text = text_filter.get("text", "").lower()
                    if not self._match_text_filter(cell_text, text, mode):
                        visible = False
                        break

            self.setRowHidden(row, not visible)
            if visible:
                visible_count += 1

        self.rows_filtered.emit(visible_count, self.rowCount())

    def _row_matches_filters(self, row: int) -> bool:
        """Check if single row matches filters"""
        if not self._active_filters:
            return True

        for col_key, filter_data in self._active_filters.items():
            if col_key not in self.columns:
                continue

            col_idx = self._get_table_index(col_key)
            if col_idx == -1:
                continue

            item = self.item(row, col_idx)
            cell_text = item.text() if item else ""

            if not filter_data.get("all_selected", True):
                allowed = filter_data.get("selected_values", [])
                if cell_text not in allowed:
                    return False

            text_filter = filter_data.get("text_filter")
            if text_filter:
                mode = text_filter.get("mode", "contains")
                text = text_filter.get("text", "").lower()
                if not self._match_text_filter(cell_text, text, mode):
                    return False

        return True

    def _match_text_filter(self, cell_text: str, text: str, mode: str) -> bool:
        """Helper for text logic"""
        cell_lower = cell_text.lower()
        if mode == "contains":
            return text in cell_lower
        elif mode == "not_contains":
            return text not in cell_lower
        elif mode == "equals":
            return cell_lower == text
        elif mode == "not_equals":
            return cell_lower != text
        elif mode == "starts_with":
            return cell_lower.startswith(text)
        elif mode == "ends_with":
            return cell_lower.endswith(text)
        return True

    def get_unique_values(self, column_key: str) -> List[str]:
        """Get unique values in a column"""
        if column_key in self._predefined_options:
            return self._predefined_options[column_key]

        col_idx = self._get_table_index(column_key)
        if col_idx == -1:
            return []

        values: Set[str] = set()
        for row in range(self.rowCount()):
            item = self.item(row, col_idx)
            val = item.text() if item else ""
            values.add(val)
        return sorted(values)

    def clear_all_filters(self):
        """Clear all active filters"""
        self._active_filters.clear()
        self._filter_header.clear_all_filter_indicators()
        for row in range(self.rowCount()):
            self.setRowHidden(row, False)
        self._save_filter_settings()
        self.filter_changed.emit(self._active_filters)

    def get_visible_columns(self) -> List[str]:
        """Get visible column keys in visual order"""
        header = self.horizontalHeader()
        visible_cols = []
        for visual_idx in range(header.count()):
            logical_idx = header.logicalIndex(visual_idx)
            if not header.isSectionHidden(logical_idx):
                visible_cols.append(self.column_order[logical_idx])
        return visible_cols

    def _on_section_moved(self, logical_idx, old_visual, new_visual):
        self._save_settings()

    def _on_section_resized(self, logical_idx, old_size, new_size):
        self._save_settings()

    def _show_column_menu(self, pos: QPoint):
        """Show show/hide columns menu"""
        menu = QMenu(self)
        for key in self.column_order:
            col = self.columns[key]
            action = QAction(col.title, menu)
            action.setCheckable(True)
            action.setChecked(col.visible)
            action.triggered.connect(
                lambda checked, k=key: self._toggle_column(k, checked)
            )
            menu.addAction(action)
        menu.exec(self._filter_header.mapToGlobal(pos))

    def _toggle_column(self, key: str, visible: bool):
        """Toggle column visibility"""
        self.columns[key].visible = visible
        self._save_settings()

        logical_idx = self.column_order.index(key)
        self.setColumnHidden(logical_idx, not visible)
        self.horizontalHeader().setSectionHidden(logical_idx, not visible)

        if hasattr(self, "_filter_header"):
            self._filter_header.set_column_filterable(
                logical_idx, self.columns[key].filterable if visible else False
            )

    def _apply_column_settings(self):
        """Apply width and stretch settings"""
        header = self.horizontalHeader()
        for idx, key in enumerate(self.column_order):
            if idx >= header.count():
                break

            col = self.columns[key]
            header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(idx, col.width)

        if hasattr(self, "_saved_header_state") and self._saved_header_state:
            try:
                header.restoreState(self._saved_header_state)
            except Exception:
                self._saved_header_state = None

    def _on_double_click(self, index):
        """Emit double click signal with Row ID"""
        item = self.item(index.row(), 0)
        if item:
            item_id = item.data(Qt.ItemDataRole.UserRole)
            if item_id:
                self.row_double_clicked.emit(item_id)

    def _on_selection_changed(self):
        sel_model = self.selectionModel()
        if sel_model:
            current = sel_model.currentIndex()
            if current.isValid():
                item = self.item(current.row(), 0)
                if item:
                    item_id = item.data(Qt.ItemDataRole.UserRole)
                    if item_id:
                        self.row_selected.emit(item_id)
                        return

            selected = sel_model.selectedIndexes()
            if selected:
                item = self.item(selected[0].row(), 0)
                if item:
                    item_id = item.data(Qt.ItemDataRole.UserRole)
                    if item_id:
                        self.row_selected.emit(item_id)

    def get_selected_id(self) -> Optional[int]:
        sel_model = self.selectionModel()
        if sel_model:
            current = sel_model.currentIndex()
            if current.isValid():
                item = self.item(current.row(), 0)
                if item:
                    return item.data(Qt.ItemDataRole.UserRole)

            selected = sel_model.selectedIndexes()
            if selected:
                item = self.item(selected[0].row(), 0)
                if item:
                    return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _get_settings_key(self, suffix: str) -> str:
        return f"table_{self.table_id}_{self.user_id}_{suffix}"

    def _save_settings(self):
        settings = QSettings()
        header = self.horizontalHeader()
        state = header.saveState()
        settings.setValue(self._get_settings_key("header_state"), state)

        col_settings = {}
        for key, col in self.columns.items():
            col_settings[key] = {"visible": col.visible, "width": col.width}
        settings.setValue(self._get_settings_key("columns"), col_settings)
        self.settings_changed.emit()

    def _load_settings(self):
        settings = QSettings()
        col_settings = settings.value(self._get_settings_key("columns"))
        if col_settings:
            for key, config in col_settings.items():
                if key in self.columns:
                    self.columns[key].visible = config.get("visible", True)
                    self.columns[key].width = config.get("width", 100)

        header_state = settings.value(self._get_settings_key("header_state"))
        if header_state:
            self._saved_header_state = header_state

    def _save_filter_settings(self):
        settings = QSettings()
        settings.setValue(self._get_settings_key("filters"), self._active_filters)

    def _load_filter_settings(self):
        settings = QSettings()
        saved_filters = settings.value(self._get_settings_key("filters"))
        if saved_filters:
            self._active_filters = saved_filters
            for col_key in self._active_filters:
                if col_key in self.columns:
                    logical_idx = self.column_order.index(col_key)
                    self._filter_header.set_filter_active(logical_idx, True)

    def apply_saved_filters(self):
        """Apply filters after loading data"""
        if self._active_filters:
            self._apply_filters()

    def set_standard_row_height(self, height: int):
        self.verticalHeader().setDefaultSectionSize(height)

    def set_user_id(self, user_id: int):
        self.user_id = user_id
        self._load_settings()
        self._apply_column_settings()

    def create_action_widget(self, item_id, actions, callbacks=None):
        """Create inline action buttons"""
        from .action_buttons import (
            create_view_button,
            create_edit_button,
            create_delete_button,
        )

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        for action in actions:
            btn = None
            if action == "view":
                btn = create_view_button(widget)
                if callbacks and "view" in callbacks:
                    btn.clicked.connect(callbacks["view"])
            elif action == "edit":
                btn = create_edit_button(widget)
                if callbacks and "edit" in callbacks:
                    btn.clicked.connect(callbacks["edit"])
            elif action == "delete":
                btn = create_delete_button(widget)
                if callbacks and "delete" in callbacks:
                    btn.clicked.connect(callbacks["delete"])

            if btn:
                layout.addWidget(btn)

        layout.addStretch()
        return widget

    def create_filters_bar(self) -> "ActiveFiltersBar":
        """Create and attach an ActiveFiltersBar"""
        from .active_filters_bar import ActiveFiltersBar
        from PyQt6.QtCore import QTimer

        bar = ActiveFiltersBar(self.parent())

        bar.filter_removed.connect(self._on_filter_cleared)
        bar.clear_all_clicked.connect(self.clear_all_filters)
        self.filter_changed.connect(
            lambda filters: bar.update_filters(
                filters, {k: c.title for k, c in self.columns.items()}
            )
        )

        def sync_filters():
            if self._active_filters:
                bar.update_filters(
                    self._active_filters, {k: c.title for k, c in self.columns.items()}
                )

        QTimer.singleShot(0, sync_filters)

        return bar

    def set_server_side_mode(self, enabled: bool):
        self.server_side_mode = enabled

    def get_backend_filters(self):
        """Convert filters (if needed for backend)"""
        filters = {}
        for col_key, filter_data in self._active_filters.items():
            col_filter = {}

            if not filter_data.get("all_selected", True):
                col_filter["selected_values"] = filter_data.get("selected_values", [])

            text_filter = filter_data.get("text_filter")
            if text_filter:
                col_filter["text_match"] = {
                    "mode": text_filter.get("mode", "contains"),
                    "text": text_filter.get("text", ""),
                }

            if col_filter:
                filters[col_key] = col_filter

        return filters
