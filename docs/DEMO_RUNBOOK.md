# SiteFlow demo runbook

PROJECT_PATH: `C:\Users\User\Desktop\siteflow`

Current operational state: [STATUS.md](STATUS.md). This file records the demo
procedure and verification evidence, not active task navigation.

## Start and health

In PowerShell, from PROJECT_PATH, start each isolated run in its own terminal:

```powershell
.\.venv\Scripts\python.exe scripts/demo_server.py --keep --port 8001
.\.venv\Scripts\python.exe scripts/demo_server.py --keep --port 8002
.\.venv\Scripts\python.exe scripts/demo_server.py --keep --port 8003
```

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

Expect `status: ok`, `sqlite: available`; use the corresponding port for runs 2/3.
Open the URL printed by the launcher. Its first JSON line identifies that run's
unique temporary directory, SQLite path and uploads root. The app's ordinary
initializer creates its schema and initial item; the launcher has no business logic.

The usual local command remains unchanged and continues to use repository data:
`.\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000`.

## Initial-state gate

Each run requires work item 1, declared ready, no evidence, no inspector
decision, `NOT_READY_FOR_INSPECTION`, `MISSING`, and `LOCKED`.

STOP if the initial state differs. Restarting the server preserves the existing
database; it does not reset it. Do not delete or manually edit that database.

`DEMO_INITIAL_STATE_RESET_MISSING` is resolved by `scripts/demo_server.py`.
It reuses the module storage settings already used by the isolated pytest fixture.
No production code, endpoint, ordinary data path, or UI has been changed by A0.
The existing local database is not a fresh demo; do not use or reset it for these runs.

## Restart and cleanup

Stop that run's server with Ctrl+C, then pass its exact printed directory:

```powershell
.\.venv\Scripts\python.exe scripts/demo_server.py --resume 'C:\Users\User\AppData\Local\Temp\siteflow-demo-<actual-suffix>' --port 8001
```

`--resume` preserves existing state and rejects ordinary local data or an
uninitialized directory. A new invocation without `--resume` creates a fresh run.
`--keep` and resumed runs retain artifacts for inspection. After the server has
stopped, those artifacts can be deleted by removing only the printed, marked
`siteflow-demo-*` temporary directory. Never remove repository `data/`.
For a disposable run, omit `--keep`; normal shutdown removes that run automatically.

## Browser actions after U002 handoff and STOP WRITES

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

## Semantic gate

Evidence validation is not engineering approval. Packet readiness is not
acceptance: `PACKET_READY_FOR_INSPECTION` must remain `LOCKED`. Only the
inspector's `CONFIRMED` decision permits `UNLOCKED`.

U002 changes only pending-validation copy in `templates/index.html`: RU says
«ещё не подтверждена человеком», KZ says «адам тарапынан әлі расталған жоқ».
Completed validation wording remains behind `VALIDATED_EVIDENCE`. Markup, CSS,
backend and routes are unchanged. Both semantic regression cases pass; their
sensitivity to the original defective template was established during remediation.

## Historical browser evidence — before file-picker correction

Codex in-app browser, desktop 1265 x 712. Transitions used visible file chooser
and explicit validation/inspector buttons, never direct SQLite writes.
Same synthetic `f003-demo-proof.txt` in all runs; upload SHA-256:
`745f6f8fed31ced99e1fb636abe927cb563cfad1f015df661cdad8310fbb4f16`.
Synthetic test decisions do not establish real-world engineering acceptance.

All roots below are direct children of `C:\Users\User\AppData\Local\Temp`;
each contains its own `data/siteflow.sqlite3` and `uploads/`.

| Run | Root | Language | Browser workflow | Seconds |
| --- | --- | --- | --- | --- |
| 1 | siteflow-demo-c5h7pqwq | RU | PASS | 20.751 |
| 2 | siteflow-demo-0ovplhv0 | KZ | PASS | 44.197 |
| 3 | siteflow-demo-sxxw2d7d | RU | PASS | 19.996 |

Each initial SQLite had item 1, `declared`, no decision/evidence, empty uploads,
and exact `NOT_READY_FOR_INSPECTION` + `LOCKED`; browser also showed `MISSING`.
Fresh DOM observations after each action proved `NEEDS_REVIEW` + `observed`,
then `VALIDATED_EVIDENCE` + `PACKET_READY_FOR_INSPECTION` + `LOCKED`,
then `CONFIRMED` + `UNLOCKED`. Prior runs and ordinary local data were unchanged.
Each final database has one evidence row (id 1), one upload and one inspector decision.
Console error/warning lists were empty. No blank page or error overlay appeared.

Refresh and actual process stop/relaunch with `--resume` passed for all three.
SQLite file hashes before/after relaunch are identical:

- Run 1: `5d90924413732d518545164698cbbbbb1afd50602052d7fdaa745a83c990b253`
- Run 2: `d3d3af70f7973aeb4d5caa92921eb8bbbdde685bbcfcdae48cb0016940f2754d`
- Run 3: `caacace1e6cbf034542a548c2788659878b76a12658579ee620daa45782f6209`

Uploads retained the same hash after relaunch. `/health` returned healthy without
changing database snapshots. Final KZ -> RU -> KZ switching preserved state.
Run artifacts are retained for review; do not reset them.

Timing is wall time from opening the file chooser on an already inspected initial
screen to the observed final state, including tool/model pauses; server startup,
initial-page inspection and persistence checks are excluded. Run 2 includes a
pause to report the localization finding. A synthetic RU judge flow under 30 s
was demonstrated; this is not a promise about real inspection duration.

## Historical failure: KZ native file input (resolved)

RUN 2 initial screenshot visibly shows Russian «Выберите файл» and «Файл не выбран»
inside the native upload input while the surrounding application is KZ.
The DOM accessibility label is correctly KZ, so HTML-only language tests miss it.
Cause: browser-owned file-input strings follow the browser locale, not the page's
language switch. This predates U002's wording-only correction, but violates the
whole-screen no-mixed-RU/KZ gate. Screenshot evidence is preserved in the task.

The approved UI handoff now supplies a localized upload presentation in
`templates/index.html`; the real native input remains in the form but is clipped.
The final checks below verify this correction without changing browser/OS locale.
The backend, route, form method and `file` field are unchanged.

## Infrastructure verification

`tests/test_demo_launcher.py` starts three independent real server processes with
unique SQLite/uploads roots, drives ordinary HTTP transitions with identical
synthetic evidence, checks exact states, then stops and relaunches each retained
run. Prior runs, local SQLite state and local uploads remain unchanged. Default
paths, unchanged routes, invalid-resume rejection and temporary cleanup are checked.

Use project Python 3.12.10, not system Python 3.14:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -v -p no:cacheprovider --basetemp (Join-Path $env:TEMP ('siteflow-pytest-' + [guid]::NewGuid().ToString('N')))
```

Use an ordinary user context able to stop its own child processes, not an admin
token. The first historical sandbox run hit a process-permission error; the
permitted rerun passed. Final verification explicitly checked a non-admin token.
These HTTP infrastructure checks are separate from the browser evidence above.
The full post-demo regression remains 11 passed (three pre-existing deprecation warnings).
SCN-HAPPY/NEGATIVE/UNKNOWN/CHANGE/FALLBACK pass; SCN-DEMO workflow passes.
`UNKNOWN != PASS` and exact dependency states are verified in isolated tests.

## Final file-picker integration evidence — 2026-09-22

In-app browser: desktop and 390 x 844 responsive checks. RU shows «Выбрать файл» /
«Файл не выбран»; KZ shows «Файлды таңдау» / «Файл таңдалмаған». Native RU strings
are not visible on the KZ screen. The real selected filename appears untranslated.
The visible label opens the real chooser; RUN 3 also verified Tab + Space.
Single-viewport screenshots show no picker/filename overlap on either language.
Screenshots/DOM evidence is retained in the execution task.

Three NEW final runs used visible browser actions, never direct SQLite writes:

| Run | OS-temp directory | Language | Workflow / refresh / relaunch |
| --- | --- | --- | --- |
| 1 | siteflow-demo-e20ao9cj | RU | PASS / PASS / PASS |
| 2 | siteflow-demo-1hqcltcj | KZ | PASS / PASS / PASS |
| 3 | siteflow-demo-re4jnzge | RU | PASS / PASS / PASS |

Each started with `declared`, no decision/evidence, empty uploads and exact
`NOT_READY_FOR_INSPECTION` / `MISSING` / `LOCKED`. Fresh DOM observations proved
`NEEDS_REVIEW` / `observed`, explicit validation to `VALIDATED_EVIDENCE` /
`PACKET_READY_FOR_INSPECTION` / `LOCKED`, then explicit inspector confirmation
to `CONFIRMED` / `UNLOCKED`. Final SQLite has exactly one evidence row (id 1)
and one upload per run. Console error/warning lists were empty.

All three uploads matched the canonical input SHA-256 recorded above. No
previous evidence/decision/unlock crossed run boundaries. Ordinary local state
and uploads remained unchanged; health calls did not change business snapshots.
Final RU/KZ switching preserved state. SQLite hashes before/after real relaunch:

- Run 1: `6f28f51762cc39f6d3ca90c0cd99386d76fd14fdbde919c4327c3bfe87055587`
- Run 2: `510c7812295c2a79ce004588508dbb390fd6349fe8133d0bd727680b16c20e78`
- Run 3: `ee65d067c07ffdea522a6433f30d46da3364b02386081ab6a34006404bf37de8`

Own canonical/demo processes were stopped using exact PID + command-line checks
under a verified non-admin user token. Terminal Ctrl+C did not propagate here;
targeted process-tree termination was used, never global taskkill or admin/UAC.
Older unrelated processes predating this run were identified and left untouched.
Run artifacts remain available for read-only review. Full pytest before/after
browser verification: 11 passed (10.19 s / 15.85 s), existing deprecation warnings only.

## PASS / FAIL

PASS requires three independently observed browser flows, identical semantic
outcomes, no carry-over of evidence/decision/stage, persistence, language checks,
regression and read-only tester approval. TestClient tests alone are not 3x browser
proof. Record `demo_under_30s` from actual browser timings, never test duration.

On FAIL preserve state/output, identify the root cause, and stop the run. Allow
one authorized minimal correction; a second failure of that root cause means STOP.
UI changes need Decision Center approval. Do not launch U002, AI, or a new feature.
