"""MessageTable — Table widget for displaying messages."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from ...core.models import Message
from ...theme.colors import Colors
from ...utils.formatters import format_datetime, truncate


class MessageTable(QTableWidget):
    """Table for displaying Discord messages with cyberpunk styling."""

    COLUMNS = ["Time", "Channel", "Content", "Attachments", "Status"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def add_message(self, message: Message, status: str = "") -> int:
        """Add a message row. Returns the row index."""
        row = self.rowCount()
        self.insertRow(row)

        # Timestamp
        time_item = QTableWidgetItem(format_datetime(message.timestamp))
        time_item.setForeground(QColor(Colors.TEXT_SECONDARY))
        self.setItem(row, 0, time_item)

        # Channel
        ch_item = QTableWidgetItem(message.channel_id[:8] + "...")
        ch_item.setForeground(QColor(Colors.ELECTRIC_PURPLE))
        self.setItem(row, 1, ch_item)

        # Content
        content_item = QTableWidgetItem(truncate(message.content, 80))
        self.setItem(row, 2, content_item)

        # Attachments
        att_count = len(message.attachments)
        att_item = QTableWidgetItem(str(att_count) if att_count else "")
        att_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 3, att_item)

        # Status
        status_item = QTableWidgetItem(status)
        if status == "Deleted":
            status_item.setForeground(QColor(Colors.SUCCESS))
        elif status == "Failed":
            status_item.setForeground(QColor(Colors.ERROR))
        elif status == "Skipped":
            status_item.setForeground(QColor(Colors.WARNING))
        self.setItem(row, 4, status_item)

        return row

    def update_status(self, row: int, status: str) -> None:
        """Update the status column for a row."""
        item = self.item(row, 4)
        if item:
            item.setText(status)
            if status == "Deleted":
                item.setForeground(QColor(Colors.SUCCESS))
            elif status == "Failed":
                item.setForeground(QColor(Colors.ERROR))
            elif status == "Skipped":
                item.setForeground(QColor(Colors.WARNING))

    def clear_messages(self) -> None:
        """Clear all message rows."""
        self.setRowCount(0)
