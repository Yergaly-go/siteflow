# Prompt Registry

Execution registry for SiteFlow.

Полные prompt bodies здесь не хранятся.

## Status vocabulary

PLANNED
IN_PROGRESS
PASS
FAIL
BLOCKED
STOPPED

UNKNOWN != PASS
NOT_RUN != PASS
NOT_VERIFIED != PASS

## Registry

| ID | Type | Owner | Goal | Status | Evidence | Commit |
| PD001 | Product | Decision chat | Freeze Product/P0 | PASS | Hidden Works Evidence Gate frozen | — |
| SD001 | Stack | Stack chat | Freeze implementation stack | PASS | FastAPI/HTMX + SQLite + multipart frozen | — |
| B001 | Bootstrap | A0 | Bootstrap repo + Git delivery | PASS | bootstrap files verified; push verified; remote SHA matched | 85c4b0a296de9897c531166cf171e6ae8f8de3bc |
| F001 | Feature | A0 | First persistent evidence-gate Green | PASS | health, deterministic scenarios, browser flow, refresh/restart persistence verified | f02f8eebc05aabd3cf8b0b2b9d2a5945b6857f0e |
| F002 | Verification | A0 | P0 scenario closure | PASS | six scenarios, pytest, browser, and restart regression verified | 09f078619395e084dae38dc9ffbdab0d0055e33d |

## Prompt IDs

Product:
PD001, PD002...

Stack:
SD001, SD002...

Bootstrap:
B001, B002...

Research:
R001, R002...

Implementation:
F001, F002...

Research + implementation:
R+F001, R+F002...

AI research:
AIR001...

AI implementation:
AIF001...

AI research + implementation:
AIR+AIF001...

## Rules

Closed F IDs не открываются повторно.

Не создавать:

F001-FIX

Correction получает следующий ID.

Каждый PASS требует observable evidence.

Commit SHA записывать только после существования commit.

Commit != Push.

Full prompts остаются в execution conversation.
