"""Test/demo-only launcher. Never resets or edits the ordinary local database."""

from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import json
from pathlib import Path
import sys
import tempfile

import uvicorn

# Support running this script directly from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
import app as siteflow  # noqa: E402

PREFIX = "siteflow-demo-"
MARKER = ".siteflow-demo-run"
MARKER_CONTENT = "siteflow-demo-v1\n"


def checked_run_directory(path: Path) -> Path:
    """Only accept a directory created by this launcher in the OS temp root."""
    if path.is_symlink() or path.is_junction():
        raise ValueError("Demo directory must not be a link")
    root = path.resolve(strict=True)
    if root.parent != Path(tempfile.gettempdir()).resolve() or not root.name.startswith(PREFIX):
        raise ValueError("Expected a siteflow-demo-* directory in the OS temp root")
    if (root / MARKER).read_text(encoding="utf-8") != MARKER_CONTENT:
        raise ValueError("Invalid demo directory marker")
    for relative in ("data", "uploads", "data/siteflow.sqlite3", MARKER):
        child = root / relative
        if child.is_symlink() or child.is_junction():
            raise ValueError("Demo storage must not contain links")
    return root


@contextmanager
def demo_directory(*, keep: bool = False, resume: Path | None = None):
    if resume is not None:
        root = checked_run_directory(resume)
        if not (root / "data/siteflow.sqlite3").is_file() or not (root / "uploads").is_dir():
            raise ValueError("Cannot resume an uninitialized run")
        yield root  # Retained runs are never deleted by --resume.
        return

    with ExitStack() as cleanup:
        root = Path(
            tempfile.mkdtemp(prefix=PREFIX)
            if keep
            else cleanup.enter_context(tempfile.TemporaryDirectory(prefix=PREFIX))
        ).resolve()
        (root / MARKER).write_text(MARKER_CONTENT, encoding="utf-8")
        yield root


@contextmanager
def isolated_app(run_directory: Path):
    """Use the same module settings as the existing isolated pytest fixture."""
    root = checked_run_directory(run_directory)
    previous = siteflow.DATA_DIR, siteflow.DATABASE, siteflow.UPLOAD_DIR
    siteflow.DATA_DIR = root / "data"
    siteflow.DATABASE = root / "data/siteflow.sqlite3"
    siteflow.UPLOAD_DIR = root / "uploads"
    try:
        yield siteflow.app
    finally:
        siteflow.DATA_DIR, siteflow.DATABASE, siteflow.UPLOAD_DIR = previous


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8001)
    retention = parser.add_mutually_exclusive_group()
    retention.add_argument("--keep", action="store_true", help="Retain artifacts for restart and inspection")
    retention.add_argument("--resume", type=Path, help="Resume a retained run, without resetting it")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    try:
        with demo_directory(keep=args.keep, resume=args.resume) as root:
            with isolated_app(root) as application:
                print(json.dumps({
                    "mode": "NON_PRODUCTION_DEMO",
                    "run_directory": str(root),
                    "sqlite": str(siteflow.DATABASE),
                    "uploads": str(siteflow.UPLOAD_DIR),
                    "url": f"http://127.0.0.1:{args.port}",
                    "retained": bool(args.keep or args.resume),
                }), flush=True)
                # Schema, seed data and all business transitions stay in app.py.
                uvicorn.run(application, host="127.0.0.1", port=args.port)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
