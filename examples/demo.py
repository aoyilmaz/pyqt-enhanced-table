import sys
import os
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QColor

# Add the parent directory to sys.path to allow importing pyqt_enhanced_table
# This allows running the example directly from the repo without installation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyqt_enhanced_table import (
    EnhancedTableWidget,
    ColumnConfig,
    NumericTableWidgetItem,
)


def main():
    app = QApplication(sys.argv)

    # Main window setup
    window = QWidget()
    window.setWindowTitle("PyQt Enhanced Table Demo")
    window.resize(900, 600)
    layout = QVBoxLayout(window)

    # Title
    title = QLabel("📦 Inventory Management Demo")
    title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
    layout.addWidget(title)

    # 1. Define Columns
    columns = [
        ColumnConfig("id", "ID", width=60, filter_type="number", sortable=True),
        ColumnConfig("name", "Product Name", width=200, filter_type="text"),
        ColumnConfig(
            "category", "Category", width=120, filter_type="enum"
        ),  # Enum filtering
        ColumnConfig("price", "Price ($)", width=100, filter_type="number"),
        ColumnConfig("stock", "Stock", width=80, filter_type="number"),
        ColumnConfig("status", "Status", width=120, filter_type="enum"),
    ]

    # 2. Initialize Table
    # table_id is used for persistence (saving column widths, filters etc.)
    table = EnhancedTableWidget(table_id="demo_inventory_table", columns=columns)

    # 3. Add Data (5 sample rows)
    data = [
        (101, "Wireless Mouse", "Electronics", 29.99, 150, "In Stock"),
        (102, "Mechanical Keyboard", "Electronics", 89.50, 45, "In Stock"),
        (103, "Ergonomic Chair", "Furniture", 199.00, 12, "Low Stock"),
        (104, "USB-C Hub", "Accessories", 45.00, 0, "Out of Stock"),
        (105, "Monitor Stand", "Furniture", 35.50, 78, "In Stock"),
    ]

    table.setRowCount(len(data))

    for row_idx, row_data in enumerate(data):
        # ID (Use NumericTableWidgetItem for proper number sorting)
        table.setItem(row_idx, 0, NumericTableWidgetItem(row_data[0]))

        # Name
        table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))

        # Category
        table.setItem(row_idx, 2, QTableWidgetItem(row_data[2]))

        # Price (Formatted string, but stored value for sort)
        price_val = row_data[3]
        price_item = NumericTableWidgetItem(price_val, f"{price_val:.2f}")
        table.setItem(row_idx, 3, price_item)

        # Stock
        table.setItem(row_idx, 4, NumericTableWidgetItem(row_data[4]))

        # Status
        status_item = QTableWidgetItem(row_data[5])
        # Add some color to status
        if row_data[5] == "Out of Stock":
            color = os.environ.get("QT_COLOR_DANGER", "#e74c3c")
            status_item.setForeground(QColor(color))  # Fallback red
        elif row_data[5] == "Low Stock":
            color = os.environ.get("QT_COLOR_WARNING", "#f1c40f")
            status_item.setForeground(QColor(color))  # Fallback yellow

        table.setItem(row_idx, 5, status_item)

    # Set predefined filter options for Enum columns (improves UX)
    table.set_filter_options("category", ["Electronics", "Furniture", "Accessories"])
    table.set_filter_options("status", ["In Stock", "Low Stock", "Out of Stock"])

    layout.addWidget(table)

    # Instructions
    hint = QLabel(
        "💡 Try clicking headers to filter, or right-click headers to toggle columns."
    )
    hint.setStyleSheet("color: gray; margin-top: 5px;")
    layout.addWidget(hint)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
