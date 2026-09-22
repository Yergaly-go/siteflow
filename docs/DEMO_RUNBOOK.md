# SiteFlow demo runbook

PROJECT_PATH: `C:\Users\User\Desktop\siteflow`

F003 status: BLOCKED. Three browser runs and timing have NOT_RUN status.

## Start and health

In PowerShell, from PROJECT_PATH, with port 8000 free:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expect `status: ok`, `sqlite: available`. Open `http://127.0.0.1:8000/`.

## Initial-state gate

Each run requires work item 1, declared ready, no evidence, no inspector
decision, `NOT_READY_FOR_INSPECTION`, `MISSING`, and `LOCKED`.

STOP if the initial state differs. Restarting the server preserves the existing
database; it does not reset it. Do not delete or manually edit that database.

Current blocker: `DEMO_INITIAL_STATE_RESET_MISSING`. The application uses fixed
`data/siteflow.sqlite3` and `data/uploads/` paths. The existing temporary-database
pytest fixture supports TestClient only; there is no browser demo setup/reset.
The inspected live database has `CONFIRMED` and two existing evidence rows.

Smallest proposed solution for Decision Center: a non-production launcher under
`tests/` using a fresh temporary SQLite/upload directory per run, based on the
existing fixture. Use the ordinary app initializer and HTTP routes; retain the
same directory for restart checks within that run. Do not implement a reset
endpoint or touch live data. This launcher is proposed, not implemented.

## Actions after the initial-state blocker is resolved

1. Start the timer on the initial screen; check the named missing photo requirement.
2. Select the same synthetic evidence file and click «Добавить доказательство».
   Expect `NEEDS_REVIEW`, `NOT_READY_FOR_INSPECTION`, `LOCKED`.
3. Explicitly confirm the evidence relation using «Подтвердить доказательство».
   Expect `VALIDATED_EVIDENCE`, `PACKET_READY_FOR_INSPECTION`, `LOCKED`.
4. Click «Зафиксировать решение инспектора» to record human confirmation.
   Expect `CONFIRMED`, `UNLOCKED`. Stop the timer and record actual seconds.
5. Refresh, then restart the same run's server and refresh again. Expect the same
   work item, evidence relation, decision and stage state.
6. Check РУС | ҚАЗ in each state: whole-screen language changes, technical IDs
   and workflow state do not. Repeat with a fresh isolated directory for runs 2/3.

## Semantic gate and known failure

Evidence validation is not engineering approval. Packet readiness is not
acceptance: `PACKET_READY_FOR_INSPECTION` must remain `LOCKED`. Only the
inspector's `CONFIRMED` decision permits `UNLOCKED`.

UI CHANGE REQUEST (requires separate approval): in `templates/index.html`, the
`NEEDS_REVIEW` section says «Человек подтвердил связь доказательства с обязательным
требованием.» / «Адам дәлелдеменің міндетті талаппен байланысын растады.» before
validation. Replace only this completed-action claim with an instruction or
pending-action description in both languages. Do not change routes or states.

Reproduced using the existing isolated-test setup and POST `/evidence`: SQLite
reports `NEEDS_REVIEW`, `observed`, no human decision, and `LOCKED`, while both
rendered language responses contain the completed-action claim. No live database
was edited. This semantic gate is FAIL; no UI fix has been made.

## PASS / FAIL

PASS requires three independently observed browser flows, identical semantic
outcomes, no carry-over of evidence/decision/stage, persistence, language checks,
regression and read-only tester approval. TestClient tests alone are not 3x browser
proof. Record `demo_under_30s` from actual browser timings, never test duration.

On FAIL preserve state/output, identify the root cause, and stop the run. Allow
one authorized minimal correction; a second failure of that root cause means STOP.
UI changes need Decision Center approval. Do not launch U002, AI, or a new feature.
