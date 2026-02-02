# PyQt Enhanced Table

A powerful, Excel-like table widget for PyQt6 applications.

## Features

- **Excel-like Filtering**: Click on column headers to filter by value or text (contains, starts with, etc.).
- **Sorting**: Multi-type sorting (numeric, text).
- **Column Management**: Reorder, resize, and hide/show columns via context menu.
- **Persistence**: Automatically saves column widths, visibility, and active filters using `QSettings`.
- **Pagination**: Integrated `TableFooter` with pagination controls and page size selector.
- **Theme Support**: Customizable colors and icons via `theme.py`.

## Installation

```bash
pip install pyqt-enhanced-table
```

## Usage

```python
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from pyqt_enhanced_table import EnhancedTableWidget, ColumnConfig

app = QApplication([])

# Define Columns
columns = [
    ColumnConfig("id", "ID", width=50, filter_type="number"),
    ColumnConfig("name", "Name", width=150),
    ColumnConfig("status", "Status", width=100, filter_type="enum"),
]

# Create Table
# table_id is used for saving settings (column width, filters, etc.)
table = EnhancedTableWidget(table_id="my_users_table", columns=columns)

# Add Data
table.setRowCount(2)
# Row 0
table.setItem(0, 0, QTableWidgetItem("1"))
table.setItem(0, 1, QTableWidgetItem("John Doe"))
table.setItem(0, 2, QTableWidgetItem("Active"))
# Row 1
table.setItem(1, 0, QTableWidgetItem("2"))
table.setItem(1, 1, QTableWidgetItem("Jane Smith"))
table.setItem(1, 2, QTableWidgetItem("Inactive"))

table.show()
app.exec()
```

## Dependencies

- PyQt6
- qtawesome (for icons)
