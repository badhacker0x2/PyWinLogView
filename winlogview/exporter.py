"""
exporter.py - Export Event Log records to various formats.

Supported formats
-----------------
* CSV   – spreadsheet-friendly
* JSON  – machine-readable
* HTML  – styled report viewable in a browser
* TXT   – plain-text log
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Sequence

from .models import EventRecord


class EventExporter:
    """
    Export a list of :class:`~winlogview.models.EventRecord` objects.

    Parameters
    ----------
    records : list[EventRecord]
        The records to export.

    Examples
    --------
    >>> exporter = EventExporter(records)
    >>> exporter.to_csv("system_errors.csv")
    >>> exporter.to_json("system_errors.json")
    >>> exporter.to_html("system_errors.html")
    """

    def __init__(self, records: Sequence[EventRecord]) -> None:
        self.records = list(records)

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------

    def to_csv(self, path: str) -> str:
        """Write records to a CSV file. Returns the absolute path."""
        fieldnames = [
            "record_id", "event_id", "log_name", "source",
            "level", "time_created", "computer", "message",
            "task", "keywords", "user_id",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in self.records:
                row = r.to_dict()
                writer.writerow(row)
        return os.path.abspath(path)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    def to_json(self, path: str, indent: int = 2) -> str:
        """Write records to a JSON file. Returns the absolute path."""
        data = [r.to_dict() for r in self.records]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=str)
        return os.path.abspath(path)

    # ------------------------------------------------------------------
    # TXT
    # ------------------------------------------------------------------

    def to_txt(self, path: str) -> str:
        """Write records to a plain-text file. Returns the absolute path."""
        with open(path, "w", encoding="utf-8") as f:
            for r in self.records:
                ts = r.time_created.strftime("%Y-%m-%d %H:%M:%S") if r.time_created else "N/A"
                f.write(
                    f"[{ts}] [{r.level:<12}] ID={r.event_id} | {r.source}\n"
                    f"  {r.message[:200]}\n\n"
                )
        return os.path.abspath(path)

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------

    def to_html(self, path: str, title: str = "Event Log Report") -> str:
        """
        Write a styled HTML report. Returns the absolute path.

        The report is self-contained (no external dependencies) and includes
        a sortable table with colour-coded severity levels.
        """
        level_colors = {
            "Critical":    ("#ff4444", "#fff"),
            "Error":       ("#ff6b6b", "#fff"),
            "AuditFailure":("#ff6b6b", "#fff"),
            "Warning":     ("#ffa726", "#000"),
            "Information": ("#42a5f5", "#fff"),
            "AuditSuccess":("#66bb6a", "#fff"),
            "Verbose":     ("#bdbdbd", "#000"),
        }

        rows_html = []
        for r in self.records:
            ts = r.time_created.strftime("%Y-%m-%d %H:%M:%S") if r.time_created else "N/A"
            bg, fg = level_colors.get(r.level, ("#e0e0e0", "#000"))
            badge = (
                f'<span style="background:{bg};color:{fg};padding:2px 8px;'
                f'border-radius:4px;font-size:0.8em;font-weight:600;">'
                f'{r.level}</span>'
            )
            msg_safe = r.message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            rows_html.append(
                f"<tr>"
                f"<td>{r.record_id}</td>"
                f"<td>{ts}</td>"
                f"<td>{badge}</td>"
                f"<td><strong>{r.event_id}</strong></td>"
                f"<td>{r.log_name}</td>"
                f"<td>{r.source}</td>"
                f"<td style='max-width:420px;word-break:break-word;'>{msg_safe[:300]}</td>"
                f"</tr>"
            )

        generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#0f1117;color:#e0e0e0;padding:24px}}
  h1{{font-size:1.6rem;margin-bottom:4px;color:#90caf9}}
  .meta{{font-size:0.85rem;color:#757575;margin-bottom:20px}}
  .summary{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
  .badge{{padding:6px 14px;border-radius:20px;font-size:0.82rem;font-weight:600}}
  table{{width:100%;border-collapse:collapse;background:#1a1d27;border-radius:8px;overflow:hidden;font-size:0.85rem}}
  thead{{background:#1e2230}}
  th{{padding:10px 12px;text-align:left;color:#90caf9;font-weight:600;border-bottom:1px solid #2a2d3e}}
  td{{padding:9px 12px;border-bottom:1px solid #1e2230;vertical-align:top}}
  tr:hover td{{background:#1e2230}}
  .filter-bar{{margin-bottom:14px;display:flex;gap:8px;flex-wrap:wrap}}
  input[type=text]{{background:#1a1d27;border:1px solid #2a2d3e;color:#e0e0e0;padding:6px 12px;border-radius:6px;font-size:0.85rem;width:260px}}
  input[type=text]:focus{{outline:none;border-color:#90caf9}}
</style>
</head>
<body>
<h1>🖥️ {title}</h1>
<p class="meta">Generated: {generated} &nbsp;|&nbsp; Total records: {len(self.records)}</p>
<div class="filter-bar">
  <input type="text" id="searchBox" placeholder="Filter by keyword…" oninput="filterTable()"/>
</div>
<table id="logTable">
<thead>
<tr>
  <th>#</th><th>Timestamp</th><th>Level</th><th>Event ID</th>
  <th>Log</th><th>Source</th><th>Message</th>
</tr>
</thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>
<script>
function filterTable(){{
  const q=document.getElementById('searchBox').value.toLowerCase();
  document.querySelectorAll('#logTable tbody tr').forEach(r=>{{
    r.style.display=r.textContent.toLowerCase().includes(q)?'':'none';
  }});
}}
</script>
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return os.path.abspath(path)