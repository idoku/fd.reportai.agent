from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class PandocDocxExporter:
    def export(
        self,
        markdown: str,
        output_path: str | Path,
        *,
        reference_doc: str | Path | None = None,
    ) -> Path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
            handle.write(markdown)
            markdown_path = Path(handle.name)

        command = [
            "pandoc",
            str(markdown_path),
            "-f",
            "markdown",
            "-t",
            "docx",
            "-o",
            str(destination),
        ]
        if reference_doc is not None:
            command.extend(["--reference-doc", str(reference_doc)])

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("pandoc is not installed or not available in PATH.") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip() or exc.stdout.strip() or "pandoc export failed.") from exc
        finally:
            markdown_path.unlink(missing_ok=True)

        return destination
