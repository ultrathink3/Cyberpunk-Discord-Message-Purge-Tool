"""ChannelTree — Server/channel tree with checkboxes for selection."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from ...core.models import Channel, ChannelType, Guild
from ...theme.colors import Colors


class ChannelTree(QTreeWidget):
    """Tree widget showing servers and channels with checkboxes."""

    selection_changed = Signal(list, list)  # guild_ids, channel_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setAlternatingRowColors(False)
        self.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)

        self._guild_items: dict[str, QTreeWidgetItem] = {}
        self._channel_items: dict[str, QTreeWidgetItem] = {}
        self._dm_root: QTreeWidgetItem | None = None

        self.itemChanged.connect(self._on_item_changed)

    def clear_tree(self) -> None:
        """Clear all items."""
        self.clear()
        self._guild_items.clear()
        self._channel_items.clear()
        self._dm_root = None

    def add_guild(self, guild: Guild, channels: list[Channel]) -> None:
        """Add a guild with its channels to the tree."""
        guild_item = QTreeWidgetItem(self)
        guild_item.setText(0, f"  {guild.name}")
        guild_item.setData(0, Qt.ItemDataRole.UserRole, ("guild", guild.id))
        guild_item.setFlags(
            guild_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        guild_item.setCheckState(0, Qt.CheckState.Unchecked)
        guild_item.setForeground(0, QColor(Colors.TEXT_PRIMARY))

        self._guild_items[guild.id] = guild_item

        # Categories
        categories: dict[str | None, QTreeWidgetItem] = {}
        for ch in channels:
            if ch.type == ChannelType.GUILD_CATEGORY:
                cat_item = QTreeWidgetItem(guild_item)
                cat_item.setText(0, f"  {ch.name.upper()}")
                cat_item.setForeground(0, QColor(Colors.TEXT_SECONDARY))
                cat_item.setFlags(
                    cat_item.flags()
                    & ~Qt.ItemFlag.ItemIsUserCheckable
                )
                categories[ch.id] = cat_item

        for ch in channels:
            if ch.type == ChannelType.GUILD_CATEGORY:
                continue
            if not ch.is_text:
                continue

            parent_item = categories.get(ch.parent_id, guild_item)
            ch_item = QTreeWidgetItem(parent_item)
            prefix = "#" if ch.type == ChannelType.GUILD_TEXT else ""
            ch_item.setText(0, f"  {prefix}{ch.name}")
            ch_item.setData(0, Qt.ItemDataRole.UserRole, ("channel", ch.id))
            ch_item.setFlags(
                ch_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            ch_item.setCheckState(0, Qt.CheckState.Unchecked)
            ch_item.setForeground(0, QColor(Colors.TEXT_SECONDARY))
            self._channel_items[ch.id] = ch_item

    def add_dm_channels(self, channels: list[Channel]) -> None:
        """Add DM channels to the tree."""
        if not channels:
            return

        self._dm_root = QTreeWidgetItem(self)
        self._dm_root.setText(0, "  Direct Messages")
        self._dm_root.setData(0, Qt.ItemDataRole.UserRole, ("dm_root", ""))
        self._dm_root.setFlags(
            self._dm_root.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        self._dm_root.setCheckState(0, Qt.CheckState.Unchecked)
        self._dm_root.setForeground(0, QColor(Colors.MAGENTA))

        for ch in channels:
            ch_item = QTreeWidgetItem(self._dm_root)
            ch_item.setText(0, f"  {ch.name}")
            ch_item.setData(0, Qt.ItemDataRole.UserRole, ("channel", ch.id))
            ch_item.setFlags(
                ch_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            ch_item.setCheckState(0, Qt.CheckState.Unchecked)
            ch_item.setForeground(0, QColor(Colors.TEXT_SECONDARY))
            self._channel_items[ch.id] = ch_item

    def get_selected(self) -> tuple[list[str], list[str]]:
        """Get selected guild IDs and channel IDs."""
        guild_ids = []
        channel_ids = []

        for guild_id, item in self._guild_items.items():
            if item.checkState(0) == Qt.CheckState.Checked:
                guild_ids.append(guild_id)

        for ch_id, item in self._channel_items.items():
            if item.checkState(0) == Qt.CheckState.Checked:
                # Only include if parent guild isn't fully selected
                parent = item.parent()
                if parent:
                    data = parent.data(0, Qt.ItemDataRole.UserRole)
                    if data and data[0] == "guild" and data[1] in guild_ids:
                        continue
                channel_ids.append(ch_id)

        return guild_ids, channel_ids

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle check state changes — propagate to children."""
        if column != 0:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        state = item.checkState(0)
        item_type = data[0]

        # Propagate check to children
        if item_type in ("guild", "dm_root"):
            self.blockSignals(True)
            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole)
                if child_data:
                    child.setCheckState(0, state)
                # Also propagate to category children
                for j in range(child.childCount()):
                    grandchild = child.child(j)
                    if grandchild.data(0, Qt.ItemDataRole.UserRole):
                        grandchild.setCheckState(0, state)
            self.blockSignals(False)

        guild_ids, channel_ids = self.get_selected()
        self.selection_changed.emit(guild_ids, channel_ids)

    def select_all(self) -> None:
        """Select all items."""
        self.blockSignals(True)
        for item in self._guild_items.values():
            item.setCheckState(0, Qt.CheckState.Checked)
        for item in self._channel_items.values():
            item.setCheckState(0, Qt.CheckState.Checked)
        if self._dm_root:
            self._dm_root.setCheckState(0, Qt.CheckState.Checked)
        self.blockSignals(False)
        guild_ids, channel_ids = self.get_selected()
        self.selection_changed.emit(guild_ids, channel_ids)

    def deselect_all(self) -> None:
        """Deselect all items."""
        self.blockSignals(True)
        for item in self._guild_items.values():
            item.setCheckState(0, Qt.CheckState.Unchecked)
        for item in self._channel_items.values():
            item.setCheckState(0, Qt.CheckState.Unchecked)
        if self._dm_root:
            self._dm_root.setCheckState(0, Qt.CheckState.Unchecked)
        self.blockSignals(False)
        self.selection_changed.emit([], [])
