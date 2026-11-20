"""Cold tier: monthly Markdown summaries derived deterministically from the warm tier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .warm import WarmStore


@dataclass
class ColdStore:
    store: WarmStore
    cold_dir: Path

    def write_monthly_summary(self, year: int, month: int) -> Path:
        # Ensure cold directory exists
        self.cold_dir.mkdir(parents=True, exist_ok=True)

        # Get counts and components
        total_defects = self.store.count_for_month(year, month)
        top_components = self.store.top_components_for_month(year, month, n=3)

        # Build the markdown content
        lines = [
            f"# {year:04d}-{month:02d}",
            "",
            f"Total defects: {total_defects}",
            "",
            "## Top components",
        ]

        for component, count in top_components:
            lines.append(f"- {component}: {count} defects")

        # Write to file
        output_path = self.cold_dir / f"{year:04d}-{month:02d}.md"
        output_path.write_text("\n".join(lines) + "\n")

        return output_path
