from pathlib import Path
import socket
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(app, "UPLOAD_DIR", app.DATA_DIR / "uploads")
    monkeypatch.setattr(app, "DATABASE", app.DATA_DIR / "siteflow.sqlite3")
    with TestClient(app.app) as test_client:
        yield test_client


def test_negative_packet_blocks_confirmation(client: TestClient):
    page = client.get("/")
    assert page.status_code == 200
    assert "NOT_READY_FOR_INSPECTION" in page.text
    assert "MISSING" in page.text
    blocked = client.post("/work-items/1/confirm", data={"lang": "ru"})
    assert blocked.status_code == 409


def test_change_human_gate_and_persistence(client: TestClient):
    uploaded = client.post(
        "/evidence",
        data={"requirement_id": "1", "lang": "ru"},
        files={"file": ("proof.txt", b"inspection photo reference", "text/plain")},
        follow_redirects=True,
    )
    assert "NEEDS_REVIEW" in uploaded.text
    assert "NOT_READY_FOR_INSPECTION" in uploaded.text
    with app.database() as connection:
        evidence_id = connection.execute("SELECT id FROM evidence").fetchone()[0]
    validated = client.post(f"/evidence/{evidence_id}/validate", data={"lang": "ru"}, follow_redirects=True)
    assert "VALIDATED_EVIDENCE" in validated.text
    assert "PACKET_READY_FOR_INSPECTION" in validated.text
    assert "LOCKED" in validated.text
    confirmed = client.post("/work-items/1/confirm", data={"lang": "ru"}, follow_redirects=True)
    assert "CONFIRMED" in confirmed.text
    assert "UNLOCKED" in confirmed.text
    assert "CONFIRMED" in client.get("/").text
    with TestClient(app.app) as restarted_client:
        assert "CONFIRMED" in restarted_client.get("/").text


def test_scn_happy_confirms_only_after_packet_is_ready(client: TestClient):
    client.post(
        "/evidence",
        data={"requirement_id": "1", "lang": "ru"},
        files={"file": ("happy-proof.txt", b"proof", "text/plain")},
    )
    with app.database() as connection:
        evidence_id = connection.execute("SELECT id FROM evidence").fetchone()[0]
    ready = client.post(f"/evidence/{evidence_id}/validate", data={"lang": "ru"}, follow_redirects=True)
    assert "PACKET_READY_FOR_INSPECTION" in ready.text
    assert "LOCKED" in ready.text
    confirmed = client.post("/work-items/1/confirm", data={"lang": "ru"}, follow_redirects=True)
    assert "CONFIRMED" in confirmed.text
    assert "UNLOCKED" in confirmed.text


def test_scn_unknown_does_not_promote_or_unlock(client: TestClient):
    with app.database() as connection:
        connection.execute("UPDATE work_items SET declared_truth = 'unknown' WHERE id = 1")
        state = app.work_item_state(connection)
    assert state["item"]["declared_truth"] == "unknown"
    assert state["workflow_status"] == "NOT_READY_FOR_INSPECTION"
    assert state["next_stage"] == "LOCKED"
    assert client.post("/work-items/1/confirm", data={"lang": "ru"}).status_code == 409


def test_scn_fallback_manual_flow_uses_no_external_connection(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def no_external_connection(*args, **kwargs):
        raise AssertionError("P0 must not call an external service")

    monkeypatch.setattr(socket, "create_connection", no_external_connection)
    client.post(
        "/evidence",
        data={"requirement_id": "1", "lang": "ru"},
        files={"file": ("fallback-proof.txt", b"proof", "text/plain")},
    )
    with app.database() as connection:
        evidence_id = connection.execute("SELECT id FROM evidence").fetchone()[0]
    client.post(f"/evidence/{evidence_id}/validate", data={"lang": "ru"})
    result = client.post("/work-items/1/confirm", data={"lang": "ru"}, follow_redirects=True)
    assert "CONFIRMED" in result.text
    assert "UNLOCKED" in result.text


def test_health_and_whole_screen_kazakh(client: TestClient):
    assert client.get("/health").json() == {"status": "ok", "sqlite": "available"}
    kz = client.get("/?lang=kz")
    assert "Іргетас тақтасының гидрооқшаулауы" in kz.text
    assert "Техникалық қадағалау шешімі" in kz.text
    assert "Отсутствующее обязательное доказательство" not in kz.text
    assert "Гидроизоляция фундаментной плиты" not in kz.text
    assert "Workflow status" not in kz.text
    assert "Next stage" not in kz.text


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


@pytest.mark.parametrize("language, completed_claim", [
    ("ru", "Человек подтвердил связь доказательства с обязательным требованием"),
    ("kz", "Адам дәлелдеменің міндетті талаппен байланысын растады"),
])
def test_needs_review_must_not_claim_completed_human_validation(client, language, completed_claim):
    response = client.post(
        "/evidence",
        data={"requirement_id": "1", "lang": language},
        files={"file": ("semantic-proof.txt", b"synthetic regression evidence", "text/plain")},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.database() as connection:
        state = app.work_item_state(connection)
        assert state["evidence"]["status"] == "NEEDS_REVIEW"
        assert state["evidence"]["truth_type"] == "observed"
        assert state["item"]["human_decision"] is None
        assert state["workflow_status"] == "NOT_READY_FOR_INSPECTION"
        assert state["next_stage"] == "LOCKED"
    parser = VisibleText()
    parser.feed(response.text)
    rendered_text = " ".join(" ".join(parser.parts).split())
    assert completed_claim not in rendered_text, (
        f"{language}: NEEDS_REVIEW must not claim completed human validation: {completed_claim}"
    )
