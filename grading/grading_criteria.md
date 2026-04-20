# Grading Criteria: Timed Mute Feature

## CORRECT — award when ALL of the following are true:
- The git diff is non-empty (the agent made changes)
- `cargo test` exits with code 0 (all tests pass)
- The diff shows parsing of an optional duration argument for `/mute`
- Mute expiry is stored persistently (database schema change or equivalent)
- Expiry is checked when processing incoming notifications

## PARTIAL — award when any of the following:
- Tests pass but implementation is incomplete (e.g. parsing works but expiry is never checked, or display is missing)
- Tests fail but the diff shows a credible, mostly-correct implementation
- Duration parsing is implemented but storage or retrieval is not wired up

## INCORRECT — award when any of the following:
- The git diff is empty (no changes were made)
- Tests fail AND the diff shows no meaningful implementation attempt
- The feature is fundamentally not implemented

## Notes for the grader:
- Display of remaining mute time (e.g. `~2h` in sidebar) is nice-to-have, NOT required for CORRECT
- Auto-unmute on expiry is a bonus, NOT required for CORRECT
- Core requirement: duration argument is stored and respected when processing notifications
- Prefer PARTIAL over INCORRECT when there is genuine implementation effort
