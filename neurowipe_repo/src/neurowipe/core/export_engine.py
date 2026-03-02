"""Message export engine supporting JSON, CSV, and TXT formats."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from ..utils.validators import sanitize_filename
from .discord_client import DiscordClient
from .exceptions import CancelledError, ExportError
from .models import ExportFormat, Message, SearchFilter
from .search_engine import SearchEngine

logger = logging.getLogger("neurowipe.export_engine")


class ExportEngine:
    """Exports Discord messages to various file formats."""

    def __init__(self, client: DiscordClient, search_engine: SearchEngine):
        self.client = client
        self.search_engine = search_engine
        self._cancelled = False
        self._on_progress: Callable[[int, int], None] | None = None
        self._on_log: Callable[[str, str], None] | None = None

    def set_callbacks(
        self,
        on_progress: Callable[[int, int], None] | None = None,
        on_log: Callable[[str, str], None] | None = None,
    ) -> None:
        self._on_progress = on_progress
        self._on_log = on_log

    def cancel(self) -> None:
        self._cancelled = True
        self.search_engine.cancel()

    def reset(self) -> None:
        self._cancelled = False
        self.search_engine.reset()

    def _log(self, level: str, message: str) -> None:
        if self._on_log:
            self._on_log(level, message)

    async def export(
        self,
        search_filter: SearchFilter,
        output_dir: Path,
        format: ExportFormat,
        organize_by_channel: bool = True,
    ) -> Path:
        """Export messages matching filter to specified format."""
        self.reset()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"neurowipe_export_{timestamp}"

        if organize_by_channel:
            export_path = output_dir / export_name
            export_path.mkdir(parents=True, exist_ok=True)
        else:
            export_path = output_dir

        self._log("INFO", f"Starting export to {format.value.upper()}...")

        total_exported = 0
        all_messages: list[dict] = []
        channel_messages: dict[str, list[dict]] = {}

        try:
            async for batch in self.search_engine.search_messages(search_filter):
                if self._cancelled:
                    raise CancelledError("Export cancelled")

                for msg in batch:
                    msg_dict = self._message_to_dict(msg)
                    all_messages.append(msg_dict)

                    ch_id = msg.channel_id
                    if ch_id not in channel_messages:
                        channel_messages[ch_id] = []
                    channel_messages[ch_id].append(msg_dict)

                    total_exported += 1

                if self._on_progress:
                    self._on_progress(total_exported, 0)

        except CancelledError:
            self._log("WARNING", "Export cancelled")
            raise

        if total_exported == 0:
            self._log("INFO", "No messages to export")
            return export_path

        # Write files
        if organize_by_channel:
            for ch_id, messages in channel_messages.items():
                ch_name = sanitize_filename(ch_id)
                self._write_messages(export_path / ch_name, messages, format)
        else:
            self._write_messages(export_path / export_name, all_messages, format)

        self._log("INFO", f"Exported {total_exported} messages to {export_path}")
        return export_path

    def _message_to_dict(self, msg: Message) -> dict:
        return {
            "id": msg.id,
            "channel_id": msg.channel_id,
            "guild_id": msg.guild_id or "",
            "author_id": msg.author_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "attachments": [a.get("url", "") for a in msg.attachments],
            "embeds_count": len(msg.embeds),
        }

    def _write_messages(
        self, base_path: Path, messages: list[dict], format: ExportFormat
    ) -> None:
        if format == ExportFormat.JSON:
            path = base_path.with_suffix(".json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)

        elif format == ExportFormat.CSV:
            path = base_path.with_suffix(".csv")
            if not messages:
                return
            fieldnames = messages[0].keys()
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for msg in messages:
                    row = {k: (str(v) if isinstance(v, list) else v) for k, v in msg.items()}
                    writer.writerow(row)

        elif format == ExportFormat.TXT:
            path = base_path.with_suffix(".txt")
            with open(path, "w", encoding="utf-8") as f:
                for msg in messages:
                    f.write(f"[{msg['timestamp']}] {msg['content']}\n")
                    if msg["attachments"]:
                        for att in msg["attachments"]:
                            f.write(f"  Attachment: {att}\n")
                    f.write("\n")
