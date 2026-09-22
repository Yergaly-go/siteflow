# P0 Scenario Evidence

## SCN-HAPPY

Given a complete packet with human-validated evidence and no inspector decision.
When the inspector confirms the work item.
Then workflow is `CONFIRMED` and the next stage is `UNLOCKED`.
Evidence: `test_scn_happy_confirms_only_after_packet_is_ready`.

## SCN-NEGATIVE

Given a work item with missing mandatory evidence.
When confirmation is requested.
Then workflow remains `NOT_READY_FOR_INSPECTION` and confirmation returns `409`.
Evidence: `test_negative_packet_blocks_confirmation`.

## SCN-UNKNOWN

Given authoritative `declared_truth = unknown` with no complete evidence packet.
When the work item is evaluated.
Then `unknown` remains `unknown`, workflow remains `NOT_READY_FOR_INSPECTION`, and the next stage remains `LOCKED`.
Evidence: `test_scn_unknown_does_not_promote_or_unlock`.

## SCN-CHANGE

Given missing evidence.
When evidence is added and a human validates its relation.
Then evidence changes from `NEEDS_REVIEW` to `VALIDATED_EVIDENCE`, packet becomes `PACKET_READY_FOR_INSPECTION`, and the next stage stays `LOCKED`.
Evidence: `test_change_human_gate_and_persistence`.

## SCN-FALLBACK

Given AI and external connections are unavailable.
When the manual evidence, validation, and inspector-decision flow runs.
Then it reaches `CONFIRMED` and `UNLOCKED` without an external call.
Evidence: `test_scn_fallback_manual_flow_uses_no_external_connection`.

## SCN-DEMO

Given one new work item with missing evidence.
When the user adds evidence, a human validates it, and the inspector confirms it.
Then the deterministic sequence is `NOT_READY_FOR_INSPECTION` → `NEEDS_REVIEW` → `VALIDATED_EVIDENCE` → `PACKET_READY_FOR_INSPECTION` with `LOCKED` → `CONFIRMED` with `UNLOCKED`.
Evidence: `test_change_human_gate_and_persistence` and live browser regression.
