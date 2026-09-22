# SiteFlow

Evidence-gated workflow for hidden works inspection, construction proof, human approval, and stage handoff.

## Product

**Hidden Works Evidence Gate**

Основной переход:

DECLARED COMPLETE
→ EVIDENCE CHECK
→ PACKET_READY_FOR_INSPECTION
→ HUMAN INSPECTION
→ CONFIRMED | CORRECTION_REQUIRED
→ NEXT STAGE

`PACKET_READY_FOR_INSPECTION` означает только:

пакет доказательств комплектен для передачи технадзору.

Это НЕ означает:

- техническое соответствие работы;
- инженерное одобрение;
- автоматическую приёмку.

## Primary user

Инженер участка / бригадир, инициирующий сдачу скрытых работ.

## Decision owner

Технадзор / уполномоченный принимающий инженер.

## P0

Один work item.

P0 должен:

1. показать mandatory evidence requirements;
2. обнаружить missing evidence;
3. оставить статус `NOT_READY_FOR_INSPECTION`;
4. принять недостающее evidence;
5. сохранить подтверждённую связь evidence ↔ requirement;
6. пересчитать статус в `PACKET_READY_FOR_INSPECTION`;
7. оставить следующий этап закрытым;
8. получить отдельное human decision;
9. после human confirmation перейти в `CONFIRMED`;
10. открыть следующий этап;
11. сохранить состояние после refresh и server restart.

## Evidence semantics

Evidence item status:

- `VALIDATED_EVIDENCE`
- `MISSING`
- `NEEDS_REVIEW`

Rules:

- AI candidate != validated evidence
- declared != confirmed
- observed != accepted
- completed != inspected
- inspected != approved
- evidence completeness != engineering approval

## Truth types

- declared
- observed
- confirmed
- unknown
- conflicting

## Human boundary

Только технадзор / уполномоченный инженер владеет:

- фактом проверки;
- инженерной оценкой;
- принятием или возвратом работы;
- подтверждением исправления;
- финальным разрешением перехода.

Система управляет evidence packet и workflow.

Система НЕ принимает скрытые работы автоматически.

## Languages

Default UI: RU
Second UI: KZ

Switch:

РУС | ҚАЗ

Localization:

whole-screen only.

Mixed RU/KZ UI запрещён.

Technical IDs, filenames и status IDs не переводятся.

KZ glyph gate:

Ә ә Ғ ғ Қ қ Ң ң Ө ө Ұ ұ Ү ү Һ һ І і

## Frozen stack

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic
- pytest
- Jinja2
- HTMX 2.0.10 local
- custom CSS
- python-multipart
- SQLite via Python sqlite3

External services для P0:

none

## Storage contract

SQLite = authoritative workflow state.

Uploaded local files = evidence artifacts.

Deterministic rules = derived workflow status.

Human decision = acceptance truth.

Не являются source of truth:

- cache
- memory
- vector DB
- AI output

Runtime storage:

data/

Uploaded evidence:

data/uploads/

## AI

AI не требуется для P0.

Если AI будет добавлен позже, он может только:

- извлекать candidates;
- предлагать evidence mapping;
- объяснять candidate;
- возвращать source references.

AI не может:

- самостоятельно валидировать engineering suitability;
- принимать скрытые работы;
- выдавать final acceptance;
- открывать next stage.

## Mandatory scenarios

- SCN-HAPPY
- SCN-NEGATIVE
- SCN-UNKNOWN
- SCN-CHANGE
- SCN-FALLBACK
- SCN-DEMO

## F001

Первый vertical Green:

missing evidence
→ NOT_READY_FOR_INSPECTION
→ add + validate evidence
→ PACKET_READY_FOR_INSPECTION
→ next stage LOCKED
→ human confirmation
→ CONFIRMED
→ next stage UNLOCKED

F001 должен пережить:

- browser refresh;
- server restart.

## Run command

python -m uvicorn app:app --host 0.0.0.0 --port 8000

## Health

GET /health

Health должен проверять доступность SQLite безопасным способом и не изменять business workflow state.

Server started != PASS.

## Current status

Product: FROZEN
Language: FROZEN
Stack: FROZEN
Git 0G: PASS
Bootstrap: IN_PROGRESS
Implementation: NOT_STARTED
Runtime: NOT_VERIFIED
F001: NOT_RUN

## Out of P0

- ERP
- CRM
- общий корпоративный чат
- generic task manager
- полный документооборот
- снабжение
- полный material management
- полный NCR workflow
- BIM
- analytics dashboard
- complex auth
- OCR
- PDF parser
- image processing
- vector DB
- graph DB
- background jobs
- external AI provider
