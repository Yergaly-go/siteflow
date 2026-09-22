"""Infrastructure checks only; these do not stand in for the three browser demos."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
from queue import Queue
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
from threading import Thread
import time

import httpx
import pytest
from fastapi.testclient import TestClient

import app
from scripts.demo_server import checked_run_directory, demo_directory, isolated_app

PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT / "scripts/demo_server.py"


def snapshot(database):
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        item = connection.execute("SELECT id, declared_truth, human_decision FROM work_items").fetchall()
        requirements = connection.execute("SELECT id, work_item_id, title FROM requirements").fetchall()
        evidence = connection.execute(
            "SELECT id, work_item_id, requirement_id, status, truth_type, stored_name FROM evidence ORDER BY id"
        ).fetchall()
    connection.close()
    return item, requirements, evidence


def live_fingerprint():
    database = PROJECT / "data/siteflow.sqlite3"
    state = snapshot(database) if database.exists() else None
    artifacts = sorted(str(path.relative_to(PROJECT)) for path in (PROJECT / "data/uploads").glob("*"))
    return state, artifacts


def exact_state(database):
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        state = app.work_item_state(connection)
    connection.close()
    return state


@contextmanager
def running_launcher(log_path, resume=None):
    with socket.socket() as port_probe:
        port_probe.bind(("127.0.0.1", 0))
        port = port_probe.getsockname()[1]
    command = [sys.executable, str(LAUNCHER), "--port", str(port)]
    command += ["--resume", str(resume)] if resume else ["--keep"]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, cwd=PROJECT, stdout=subprocess.PIPE, stderr=log,
            text=True, encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            lines = Queue()
            Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True).start()
            manifest = json.loads(lines.get(timeout=20))
            deadline = time.monotonic() + 20
            with httpx.Client(base_url=manifest["url"], timeout=1, trust_env=False) as client:
                while True:
                    assert process.poll() is None, log_path.read_text(encoding="utf-8")
                    try:
                        health = client.get("/health")
                        if health.status_code == 200:
                            assert health.json() == {"status": "ok", "sqlite": "available"}
                            break
                    except httpx.TransportError:
                        pass
                    assert time.monotonic() < deadline, "Demo server did not become healthy"
                    time.sleep(0.05)
                yield manifest, client
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    # Stop only this test-owned launcher and its Python child.
                    result = subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True, timeout=15,
                    )
                    assert result.returncode == 0, result.stderr
                else:
                    process.terminate()
                process.wait(timeout=15)
            process.stdout.close()


def test_default_paths_and_routes_unchanged_and_temporary_cleanup():
    defaults = (app.DATA_DIR, app.DATABASE, app.UPLOAD_DIR)
    assert defaults == (app.ROOT / "data", app.ROOT / "data/siteflow.sqlite3", app.ROOT / "data/uploads")
    routes = [(route.path, getattr(route, "methods", None)) for route in app.app.routes]
    with demo_directory() as root:
        assert root.parent == Path(tempfile.gettempdir()).resolve()
        with isolated_app(root) as application:
            with TestClient(application) as client:
                assert client.get("/").status_code == 200
                assert app.DATABASE.is_file()
                assert app.UPLOAD_DIR.is_dir()
                assert [(route.path, getattr(route, "methods", None)) for route in application.routes] == routes
    assert not root.exists()  # Only this newly created temporary run is removed.
    assert (app.DATA_DIR, app.DATABASE, app.UPLOAD_DIR) == defaults


def test_resume_rejects_local_data_and_uninitialized_runs():
    with pytest.raises(ValueError):
        with demo_directory(resume=app.DATA_DIR):
            pytest.fail("Local data directory must never be accepted as a demo run")
    with demo_directory() as root:
        with pytest.raises(ValueError, match="uninitialized"):
            with demo_directory(resume=root):
                pytest.fail("Resume must not silently seed a new run")


def test_three_isolated_launcher_processes_and_relaunch(tmp_path):
    before = live_fingerprint()
    completed = []
    roots = []
    success = False
    try:
        for number, language in enumerate(("ru", "kz", "ru"), start=1):
            with running_launcher(tmp_path / f"run-{number}.log") as (manifest, client):
                root = checked_run_directory(Path(manifest["run_directory"]))
                roots.append(root)
                database = Path(manifest["sqlite"])
                uploads = Path(manifest["uploads"])
                assert manifest["mode"] == "NON_PRODUCTION_DEMO"
                assert database == root / "data/siteflow.sqlite3"
                assert uploads == root / "uploads"
                assert len(set(roots)) == number
                initial = snapshot(database)
                assert initial[0] == [(1, "declared", None)]
                assert len(initial[1]) == 1
                assert initial[2] == []
                assert list(uploads.iterdir()) == []
                state = exact_state(database)
                assert (state["workflow_status"], state["next_stage"]) == ("NOT_READY_FOR_INSPECTION", "LOCKED")
                assert client.get("/").status_code == 200
                assert client.post("/work-items/1/confirm").status_code == 409
                result = client.post(
                    "/evidence", data={"requirement_id": "1", "lang": language},
                    files={"file": ("demo-proof.txt", b"same synthetic evidence for each isolated run", "text/plain")},
                    follow_redirects=True,
                )
                assert result.status_code == 200
                state = exact_state(database)
                evidence_id = state["evidence"]["id"]
                assert evidence_id == 1
                assert (state["evidence"]["status"], state["evidence"]["truth_type"]) == ("NEEDS_REVIEW", "observed")
                assert state["item"]["human_decision"] is None
                assert (state["workflow_status"], state["next_stage"]) == ("NOT_READY_FOR_INSPECTION", "LOCKED")
                assert client.post("/work-items/1/confirm").status_code == 409
                assert len(list(uploads.iterdir())) == 1
                assert client.post(f"/evidence/{evidence_id}/validate", data={"lang": language}).status_code == 303
                state = exact_state(database)
                assert state["evidence"]["status"] == "VALIDATED_EVIDENCE"
                assert state["item"]["human_decision"] is None
                assert (state["workflow_status"], state["next_stage"]) == ("PACKET_READY_FOR_INSPECTION", "LOCKED")
                ready = snapshot(database)
                for page_language in ("ru", "kz"):
                    page = client.get(f"/?lang={page_language}")
                    assert page.status_code == 200
                    assert f'<html lang="{page_language}">' in page.text
                    assert snapshot(database) == ready
                assert client.post("/work-items/1/confirm", data={"lang": language}).status_code == 303
                state = exact_state(database)
                assert (state["workflow_status"], state["next_stage"]) == ("CONFIRMED", "UNLOCKED")
                assert state["item"]["human_decision"] == "CONFIRMED"
                confirmed = snapshot(database)
                for _ in range(2):
                    assert client.get("/").status_code == 200
                    assert snapshot(database) == confirmed
            with running_launcher(tmp_path / f"resume-{number}.log", resume=root) as (resumed, client):
                assert Path(resumed["sqlite"]) == database
                assert client.get("/").status_code == 200
                assert snapshot(database) == confirmed
                state = exact_state(database)
                assert (state["workflow_status"], state["next_stage"]) == ("CONFIRMED", "UNLOCKED")
            completed.append((database, confirmed))
            for previous_database, previous_state in completed:
                assert snapshot(previous_database) == previous_state
        assert live_fingerprint() == before
        success = True
    finally:
        if success:
            for root in roots:
                checked = checked_run_directory(root)
                assert checked.parent == Path(tempfile.gettempdir()).resolve()
                shutil.rmtree(checked)  # Explicit, validated test-created directories only.
        else:
            print("Retained failing infrastructure run directories:", [str(root) for root in roots])
