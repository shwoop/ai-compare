# Task

You have been given a Rust codebase. Your job is to implement the following enhancement.

<issue>
## Summary

`/mute` currently toggles mute on/off permanently. Supporting a duration (e.g. `/mute 1h`, `/mute 8h`, `/mute 1d`) would let users temporarily silence a busy conversation without having to remember to unmute it later.

## Details

- Extend `/mute` to accept an optional duration argument: `/mute 1h`, `/mute 8h`, `/mute 1d`, `/mute 1w`
- `/mute` with no argument toggles permanent mute (current behavior)
- Store the mute expiry timestamp in the database
- Check mute expiry when processing incoming notifications
- Show remaining mute time in the sidebar indicator or status bar (e.g. `~2h`)
- Auto-unmute when the duration expires

</issue>

Follow KISS and DRY principles.
Your submission will be graded.
