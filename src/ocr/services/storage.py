from pathlib import Path
from datetime import datetime
import shutil
import json
from typing import Optional

class RunStorage():
    """
    Filesystem gateway for a single pipeline run.
    """
    def __init__(self, base_dir: Path, pdf_path: Path) -> None:
        """
        Initialize RunStorage for managing a single pipeline run.
        
        Args:
            base_dir: Absolute path to the base output directory
            pdf_path: Absolute path to the input PDF file
        """
        if not base_dir.is_absolute():
            raise ValueError("base_dir must be absolute. Pass Settings.output_dir")
        if not pdf_path.is_absolute():
            raise ValueError("pdf_path must be absolute. Pass Settings.pdf_path")

        self.base_dir = base_dir
        self.pdf_path = pdf_path
        # Absolute paths will be set after create_run_dir()
        self.run_dir = None
        self.pages_dir = None
        self.batches_dir = None

    def create_run_dir(self) -> Path:
        """
        Create the run folder and initial subfolders.

        - Folder name format: "DD_MM_YYYY-HH_MM_SS"
        - Creates subfolders: "pages/" and "batches/"
        - Copies the input PDF into the run folder as "input(<original_stem>).pdf"
        """
        # Ensure base directory exists, then create run folder
        self.base_dir.mkdir(parents=True, exist_ok=True)
        dir_name = datetime.now().strftime("%d_%m_%Y-%H_%M_%S")
        run_dir_abs = self.base_dir / Path(dir_name)
        run_dir_abs.mkdir()

        # Create pages and batches folders (under run root)
        pages_abs = run_dir_abs / "pages"
        batches_abs = run_dir_abs / "batches"
        pages_abs.mkdir()
        batches_abs.mkdir()

        # Copy input PDF preserving original stem
        original_stem = self.pdf_path.stem
        shutil.copy2(
            self.pdf_path, 
            run_dir_abs / f"input({original_stem}).pdf"
        )

        # Persist absolutes
        self.run_dir = run_dir_abs
        self.pages_dir = pages_abs
        self.batches_dir = batches_abs

        return run_dir_abs

    def write_image(self, page_index: int, data: bytes) -> Path:
        """
        Write a rendered page image under pages/ using a canonical name (PNG).

        File name format: pages/page_{page_index:04d}.png
        """
        if self.pages_dir is None:
            raise AttributeError("Run directory not initialized. Call create_run_dir() first.")
        target = self.pages_dir / f"page_{page_index:04d}.png"
        target.write_bytes(data)
        return target

    def create_batch(self, start_page_index: int, end_page_index: int) -> str:
        """
        Create a batch directory named by the inclusive page index range and return its batch_id.

        - Naming policy: "{start:04d}-{end:04d}" (0-based inclusive)
        """
        if start_page_index > end_page_index:
            raise ValueError("start_page_index must be <= end_page_index")
        if self.batches_dir is None:
            raise AttributeError("Run directory not initialized. Call create_run_dir() first.")
        batch_id = f"{start_page_index:04d}-{end_page_index:04d}"
        batch_dir = self.batches_dir / batch_id
        batch_dir.mkdir(parents=True)
        return batch_id

    def write_prompt(self, batch_id: str, content_md: str) -> Path:
        """Write prompt markdown under batches/{batch_id}/prompt.md.

        Requires the batch directory to exist (call create_batch first).
        """
        self._validate_batch_id(batch_id)
        if self.batches_dir is None:
            raise AttributeError("Run directory not initialized. Call create_run_dir() first.")
        batch_dir = self.batches_dir / batch_id
        if not batch_dir.exists():
            raise FileNotFoundError(f"Batch directory does not exist: {batch_dir}. Call create_batch first.")
        target = batch_dir / "prompt.md"
        target.write_text(content_md, encoding="utf-8")
        return target

    def write_response(self, batch_id: str, response_json: dict) -> Path:
        """Write LLM response JSON under batches/{batch_id}/response.json.

        Use the same method for both normal and halt responses.
        Requires the batch directory to exist (call create_batch first).
        """
        self._validate_batch_id(batch_id)
        if self.batches_dir is None:
            raise AttributeError("Run directory not initialized. Call create_run_dir() first.")
        batch_dir = self.batches_dir / batch_id
        if not batch_dir.exists():
            raise FileNotFoundError(f"Batch directory does not exist: {batch_dir}. Call create_batch first.")
        target = batch_dir / "response.json"
        target.write_text(json.dumps(response_json, indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    def write_final_excel(self, data: bytes) -> Path:
        """Write final Excel output to run root as final.xlsx (bytes only)."""
        if self.run_dir is None:
            raise AttributeError("Run directory not initialized. Call create_run_dir() first.")
        target = self.run_dir / "output.xlsx"
        target.write_bytes(data)
        return target

    def _validate_batch_id(self, batch_id: str) -> None:
        """Very conservative validation to avoid path traversal in batch_id."""
        if not batch_id or "-" not in batch_id:
            raise ValueError("batch_id must contain at least one dash, e.g., '0000-0002'")
        allowed = set("0123456789-")
        if any(ch not in allowed for ch in batch_id):
            raise ValueError("batch_id may contain only digits and dashes")
