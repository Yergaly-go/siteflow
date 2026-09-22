from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATABASE = DATA_DIR / "siteflow.sqlite3"

TEXT = {
    "ru": {
        "title": "SiteFlow — скрытые работы",
        "language": "Язык",
        "work_item": "Работа",
        "packet": "Пакет доказательств",
        "missing": "Отсутствующее обязательное доказательство",
        "add": "Добавить доказательство",
        "validate": "Подтвердить соответствие требованию",
        "review": "Доказательство ожидает проверки",
        "validated": "Доказательство подтверждено",
        "human": "Решение технадзора",
        "confirm": "Подтвердить работу",
        "locked": "Следующий этап: закрыт",
        "unlocked": "Следующий этап: открыт",
        "boundary": "Готовность пакета означает только комплектность доказательств для передачи технадзору. Это не техническое одобрение и не разрешение следующего этапа.",
        "upload_hint": "Выберите файл доказательства",
        "submit": "Сохранить доказательство",
        "truth": "Тип истины",
        "workflow_status": "Статус workflow",
        "next_stage": "Следующий этап",
        "work_name": "Гидроизоляция фундаментной плиты",
        "requirement_name": "Фото скрытой гидроизоляции до обратной засыпки",
    },
    "kz": {
        "title": "SiteFlow — жасырын жұмыстар",
        "language": "Тіл",
        "work_item": "Жұмыс",
        "packet": "Дәлелдемелер пакеті",
        "missing": "Жетіспейтін міндетті дәлелдеме",
        "add": "Дәлелдеме қосу",
        "validate": "Талапқа сәйкестігін растау",
        "review": "Дәлелдеме тексеруді күтуде",
        "validated": "Дәлелдеме расталды",
        "human": "Техникалық қадағалау шешімі",
        "confirm": "Жұмысты растау",
        "locked": "Келесі кезең: жабық",
        "unlocked": "Келесі кезең: ашық",
        "boundary": "Пакеттің дайындығы тек техникалық қадағалауға берілетін дәлелдемелердің толықтығын білдіреді. Бұл техникалық мақұлдау да, келесі кезеңге рұқсат та емес.",
        "upload_hint": "Дәлелдеме файлын таңдаңыз",
        "submit": "Дәлелдемені сақтау",
        "truth": "Ақиқат түрі",
        "workflow_status": "Workflow мәртебесі",
        "next_stage": "Келесі кезең",
        "work_name": "Іргетас тақтасының гидрооқшаулауы",
        "requirement_name": "Кері көмуге дейінгі жасырын гидрооқшаулаудың фотосы",
    },
}


class HealthResponse(BaseModel):
    status: str
    sqlite: str


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database() -> sqlite3.Connection:
    connection = connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    with database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS work_items (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                declared_truth TEXT NOT NULL,
                human_decision TEXT
            );
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY,
                work_item_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                FOREIGN KEY (work_item_id) REFERENCES work_items(id)
            );
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY,
                work_item_id INTEGER NOT NULL,
                requirement_id INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                status TEXT NOT NULL,
                truth_type TEXT NOT NULL,
                FOREIGN KEY (work_item_id) REFERENCES work_items(id),
                FOREIGN KEY (requirement_id) REFERENCES requirements(id)
            );
            """
        )
        if connection.execute("SELECT COUNT(*) FROM work_items").fetchone()[0] == 0:
            connection.execute(
                "INSERT INTO work_items (id, title, declared_truth) VALUES (1, ?, 'declared')",
                ("Гидроизоляция фундаментной плиты",),
            )
            connection.execute(
                "INSERT INTO requirements (id, work_item_id, title) VALUES (1, 1, ?)",
                ("Фото скрытой гидроизоляции до обратной засыпки",),
            )


def work_item_state(connection: sqlite3.Connection) -> dict:
    item = connection.execute("SELECT * FROM work_items WHERE id = 1").fetchone()
    requirement = connection.execute("SELECT * FROM requirements WHERE work_item_id = 1").fetchone()
    evidence = connection.execute(
        "SELECT * FROM evidence WHERE work_item_id = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    validated = evidence is not None and evidence["status"] == "VALIDATED_EVIDENCE"
    if item["human_decision"] == "CONFIRMED":
        workflow_status = "CONFIRMED"
    elif validated:
        workflow_status = "PACKET_READY_FOR_INSPECTION"
    else:
        workflow_status = "NOT_READY_FOR_INSPECTION"
    return {
        "item": item,
        "requirement": requirement,
        "evidence": evidence,
        "workflow_status": workflow_status,
        "next_stage": "UNLOCKED" if workflow_status == "CONFIRMED" else "LOCKED",
        "missing": not validated,
    }


app = FastAPI(title="SiteFlow")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        with connect() as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as error:
        raise HTTPException(status_code=503, detail="SQLite unavailable") from error
    return HealthResponse(status="ok", sqlite="available")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, lang: str = "ru") -> HTMLResponse:
    language = lang if lang in TEXT else "ru"
    with database() as connection:
        state = work_item_state(connection)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"state": state, "lang": language, "text": TEXT[language]},
    )


@app.post("/evidence")
async def add_evidence(
    file: UploadFile = File(...),
    requirement_id: int = Form(...),
    lang: str = Form("ru"),
) -> RedirectResponse:
    if requirement_id != 1 or not file.filename:
        raise HTTPException(status_code=400, detail="Invalid evidence")
    suffix = Path(file.filename).suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    content = await file.read()
    (UPLOAD_DIR / stored_name).write_bytes(content)
    with database() as connection:
        connection.execute(
            """INSERT INTO evidence
               (work_item_id, requirement_id, original_name, stored_name, status, truth_type)
               VALUES (1, 1, ?, ?, 'NEEDS_REVIEW', 'observed')""",
            (Path(file.filename).name, stored_name),
        )
    return RedirectResponse(url=f"/?lang={lang}", status_code=303)


@app.post("/evidence/{evidence_id}/validate")
def validate_evidence(evidence_id: int, lang: str = Form("ru")) -> RedirectResponse:
    with database() as connection:
        updated = connection.execute(
            """UPDATE evidence SET status = 'VALIDATED_EVIDENCE', truth_type = 'confirmed'
               WHERE id = ? AND work_item_id = 1 AND requirement_id = 1 AND status = 'NEEDS_REVIEW'""",
            (evidence_id,),
        ).rowcount
    if updated != 1:
        raise HTTPException(status_code=409, detail="Evidence cannot be validated")
    return RedirectResponse(url=f"/?lang={lang}", status_code=303)


@app.post("/work-items/1/confirm")
def confirm_work_item(lang: str = Form("ru")) -> RedirectResponse:
    with database() as connection:
        state = work_item_state(connection)
        if state["workflow_status"] != "PACKET_READY_FOR_INSPECTION":
            raise HTTPException(status_code=409, detail="Evidence packet is not ready")
        connection.execute("UPDATE work_items SET human_decision = 'CONFIRMED' WHERE id = 1")
    return RedirectResponse(url=f"/?lang={lang}", status_code=303)
