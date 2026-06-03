# Roadmap — animation, live content & live voice

> Where Clawd goes after the MVP. Four threads, built in order, each standing on
> the last. This is the durable plan; check items off as they land.

## The core idea: split **mood** from **content**

Today Clawd *is* his `State` — one enum drives sprite + sound, and that's the
whole world. Everything we want next (progress bars, finished-agent tallies,
PR/merge announcements, spoken status) needs a **second axis**:

```
  base mood        what Clawd is feeling   (idle / thinking / sleeping / happy …)
    + overlay      persistent data viz     (progress bar, count badge)
    + takeover     a one-shot big moment   (PR MERGED 🎉, agent-came-home)
    → compositor   flattens all of it to one 16×16 frame each tick
```

Plus a **generic ingestion surface** — `clawd notify` / `POST /event` — so *any*
source (git hook, GitHub poller, CI script, another Claude session) can feed him,
not just the five hardcoded Claude Code hooks. That endpoint is what turns Clawd
from "5 canned reactions" into a live status display.

### Hardware reality (from [FINDINGS.md](FINDINGS.md)) that shapes every choice
- **16×16, palette-quantized.** Numbers/labels need a tiny font; long text scrolls.
- **Host-driven frame push** (`bridge.push_image`, ~30–100 ms on screen) is the
  default — interruptible, reactive. The unused native `push_animation`
  (device-side loop upload) is the path for smooth *ambient* loops that don't need
  to interrupt fast.
- **Audio: warm ~650 ms / cold ~1.2 s; live `say` ~1.7 s.** Voice is ambient
  character, not tight sync. Pre-warm dynamic phrases to stay in the warm regime.
- **Input is claps only** (buttons are a dead channel). Events come from hooks /
  pollers / the new event endpoint, not the device.

---

## Phase 1 — Foundation (the drawing/compositor spine) — ✅ **done**

Self-contained, no hardware needed (builds + verifies under `--simulate` and the
PNG/GIF preview renderer). Unlocks Phases 2–4.

- **`render/canvas.py`** — a 16×16 `Canvas` builder: bounds-safe `set_pixel`,
  `hline/vline/rect`, `blit_sprite` (char-grid sprite with a transparent key +
  offset), `blit_frame`, `to_frame() → 256 RGB`. A transient builder that freezes
  to an immutable frame (domain data stays immutable).
- **`render/font.py`** — a 3×5 pixel font (digits, A–Z, `% + - → ♥`),
  `draw_text`, `text_width`, and a `scroll` helper for strings wider than 16 px.
- **`render/compositor.py`** — `compose(base, overlays) → 256 RGB`. Frozen overlay
  dataclasses: `ProgressBar(value, row, colors)`, `CountBadge(count, corner)`.
- **State-machine wiring** — `PetController` gains an immutable overlay set
  (`set_overlay` / `clear_overlay`) composited per frame, and a one-shot
  `play_takeover(anim)` queue that plays then resumes the mood loop. Existing
  state loop stays intact.
- **Generic event surface** — `POST /event {kind, value, text, …}` + a
  `clawd notify` CLI, mapping to overlays / takeovers / voice.
- **Composited preview renderer** — extend the preview tooling to render
  Clawd + overlays + takeovers to PNG/GIF (our stand-in for hardware), with
  proof images.

**Done when:** tests green, and preview GIFs show Clawd with a live progress bar,
a count badge, and a "MERGED" takeover.

## Phase 2 — Live content (data → glyphs) — ✅ **done**

Rides entirely on Phase 1.

- **Progress bars** — ✅ **TodoWrite** drives a real bar (N todos, M done): the
  hook parses the todo list on `PostToolUse` and posts `progress`.
- **Finished agents** — ✅ the **`SubagentStop`** hook ticks a daemon-side tally →
  a corner `CountBadge` + the poke delight reaction; `SessionStart` resets it.
- **PR / merge / CI** — ✅ `clawd watch` (a `gh`-backed poller, repo-aware so the
  global daemon stays repo-agnostic) turns PR/CI transitions into events: new PR,
  CI red/green, merged → banner (+ mood + voice). Pure `diff()` is unit-tested.
- Generic `clawd notify` surface documented in the README for custom sources.

## Phase 3 — Animations: predefined PNG/GIF + procedural — ✅ **done**

- ✅ Asset pipeline (`render/assets.py`): drop a PNG/GIF in `assets/`, `clawd
  assets build` downscales to 16×16 and writes compact JSON manifests; the daemon
  loads them stdlib-only into an `AssetLibrary`. Play via `notify play <name>`.
- ✅ Procedural "live-created" kit (`render/effects.py`): confetti, fireworks,
  plasma, pulse, sparkle/celebrate-over-Clawd. Play via `notify effect <name>`.
- *Follow-up:* native `push_animation` device-side upload for ambient loops — the
  bridge method exists, but it fights the host-driven render loop, so deferred.

## Phase 4 — Live voice — ✅ **done**

- ✅ **`POST /say`** + `clawd say "…"` + an event `say` field: arbitrary dynamic
  TTS, rendered via `say`, routed to the Ditoo, cached so a phrase is warm after
  first use (`SoundPlayer.say`, `render_say_to_wav`, `_phrase_slug`).
- ✅ A **warm vocabulary** (`VOCAB`) of common announcements is pre-rendered in a
  background thread at startup, so the live-content moments speak in the warm
  ~650 ms regime instead of paying the ~1.7 s cold `say`.
- ✅ Wired to events: `clawd watch` now speaks "Pull request merged!" / "Tests are
  failing." etc. (all warm) alongside the banners.

---

## All four phases shipped — verified on real hardware.

### Follow-up round (polish · signals · content · hands-free) — ✅ **done**
- **Polish:** overlays/banner are tunable per-call; on-device comparison confirmed
  the defaults (1px bar, dark-backed badge).
- **More content:** `effects.py` gained starfield / matrix rain / spinner / rainbow.
- **More signals:** a procedural stacked HH:MM clock (`render/clock.py`, `notify
  clock`); git-hook + test-result + launchd recipes in [`examples/`](examples/).
- **Hands-free:** launchd watcher template + git hooks; the menu-bar app already
  owns login autostart.

### Multi-session fleet bar — ✅ **done**
- One daemon serves all sessions, so a bottom strip of dots shows each session's
  state (running / needs-input / finished / idle), keyed by `session_id` with TTL
  expiry. `daemon/sessions.py` registry + `SessionBar` overlay; hooks carry the
  id; `/session` + `/sessions` endpoints; `clawd session|sessions` CLI.

### Still open
- Native `push_animation` device-side upload for ambient asset loops.
- Number-word voice for arbitrary agent counts (>5) without a cold `say`.
- "Active repo" auto-detection for `clawd watch` (today it follows a fixed repo).
- Per-session blink for "needs input" (needs the render loop to tick faster).

---

## Design rules carried from the MVP
- Daemon stays **stdlib-only at runtime** (PIL is preview-time only, lazily imported).
- **Immutable** domain data (frozen dataclasses, `merged()`-style copies). The
  `Canvas` is the one sanctioned transient builder; it produces immutable frames.
- **Many small files**, high cohesion. New code lives under `divoom_pet/render/`.
- **TDD**, `unittest`, AAA structure, matching the existing test style.
