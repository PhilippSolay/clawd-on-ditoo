# Clawd — demo flow (AI developers · ~8–10 min deep dive)

> **Goal:** take the room from "cute crab" → "ambient awareness of my whole fleet
> of AI coding sessions" → "open, hackable platform" → "and here's the clever
> engineering." **Audience:** AI developers (Claude Code / agents daily).
>
> **Format:** ~8–10 min deep dive. **Act 2 is a real live Claude Code session**
> (with a scripted fallback). Acts 1, 3–5, 7 are driven by the
> `clawd demo --show` runner (teleprompter + perfectly-timed triggers). Act 6 is a
> live architecture code-walk.

---

## Setup (before stage)

- [ ] Ditoo **on**, paired, daemon running (menu-bar app → Start Clawd), **sound on,
      routed to the Ditoo**, volume up. Quiet-ish room.
- [ ] Everything merged to `main`, daemon restarted (front-facing crab, voice
      alerts, bubbly theme live).
- [ ] Hooks installed globally (`clawd install-hooks`).
- [ ] Terminals: **(A)** the `clawd demo --show` runner, **(B)** a live Claude Code
      session for Act 2, **(C)** an editor open to the files in Act 6.
- [ ] Pre-warm the project names you'll speak (so the first alert isn't a cold ~1.7 s `say`).
- [ ] Camera on the Ditoo (so the room sees the 16×16).

---

## The flow

### Act 1 — Meet Clawd (≈30 s) · *the hook*
- **Screen:** idle — breathing, blink, the occasional look-around / bubble.
- **Do:** let him idle; **clap once** (poke + heart + chirp), **clap twice** (nap).
- **Say:** *"This is Clawd. He lives on a $40 retro Bluetooth speaker, he reacts to
  your code in real time, and he's the most emotionally available coworker you'll
  have. Clap…"* *(clap → startle + heart).*

### Act 2 — He *is* your coding session (≈90 s) · *the core* · **LIVE**
- **Screen:** Clawd at his laptop (front-facing, typing) → gear on each tool call →
  a **progress bar** fills under him → hearts + a "done" chime when it finishes.
- **Do (live, terminal B):** run a small real task — e.g.
  *"add a `slugify` helper and a test, then run the tests."* It writes a TodoWrite
  list, edits files (gear), runs tests (gear), finishes (happy).
- **Say:** *"Everything here is Claude Code hooks → a 16×16 display, live. He types
  when Claude types, throws a gear on every tool call, and that bar is his actual
  todo list completing. No polling — it's the hook stream."*
- **Fallback (if live wanders):** the runner's `[f]` key fires the scripted
  coding → tool → progress → done sequence.

### Act 3 — The fleet (≈60 s) · *the AI-dev "aha"* · runner
- **Screen:** a strip of dots along the bottom — one per session — then one goes
  **red** and Clawd **speaks**.
- **Runner cues:** seeds `web running` · `api running` · `infra finished`, beat,
  then `web needs_input` → **"web needs your input."**
- **Say:** *"You don't run one session — you run five. One daemon serves all of
  them, so this strip is your whole fleet at a glance: amber working, green done,
  red needs you. And it doesn't just show it —"* *(red + voice)* *"— it tells you
  which one, by name, out loud."*

### Act 4 — Ship it (≈30 s) · *the payoff* · runner
- **Screen:** confetti + scrolling **"MERGED"**, spoken.
- **Runner cue:** `banner "MERGED" --mood happy --say "Pull request merged!"` + confetti.
- **Say:** *"And when a session ships — confetti, and he says it out loud. In a real
  repo, `gh pr create` triggers this automatically."*

### Act 5 — It's a platform, not a toy (≈50 s) · runner
- **Screen:** rapid-fire — effect, live theme swap, drop-in GIF, clock.
- **Runner cues (call them as they fire):** `effect fireworks` ·
  `config set sounds.theme music_box` · `play <gif>` · `clock`.
- **Say:** *"All of that is one generic endpoint — `clawd notify`. Any script, any
  agent, your CI, a git hook — anything drives him. The daemon is zero-dependency
  Python. The whole thing is hackable."*

### Act 6 — Architecture code-walk (≈3 min) · *for the devs* · **LIVE in editor**
Open these in terminal C and talk; fire one live trigger per point from the runner.

1. **Mood vs content** — `divoom_pet/render/compositor.py`.
   *"One axis is his mood — a state machine. The second is content: overlays like a
   progress bar, a count badge, the session strip — frozen dataclasses with a
   `draw(canvas)`. `compose(base, overlays)` flattens both to one 256-pixel frame."*
   → live: `clawd notify progress 0.5` while pointing at `ProgressBar`.
2. **The event surface + hooks** — `divoom_pet/daemon/server.py` `_handle_event`,
   `divoom_pet/hooks/clawd-hook`.
   *"Claude Code fires a hook → `curl localhost:7878` → one generic `/event`
   endpoint. That's the whole integration. Fire-and-forget, 0.4 s timeout, never
   blocks Claude."* → live: `clawd notify banner "HELLO DEVS"`.
3. **Multi-session** — `divoom_pet/daemon/sessions.py`.
   *"One daemon, every session keyed by `session_id` with TTL expiry. That's how the
   fleet strip works — and why the voice can name the project."* → live: `clawd session demo running`.
4. **The render loop** — `divoom_pet/daemon/state_machine.py`.
   *"A background thread renders the current mood, composites overlays per frame, and
   plays one-shot 'takeovers' (the MERGED banner) before resuming. Interruptible, so
   state changes are instant."*
5. **The catch — Bluetooth-only** — `FINDINGS.md`, `ditoo_bridge/` `ditoo_audio/`
   `ditoo_ears/`, `divoom_pet/protocol/divoom.py`.
   *"The Ditoo is Bluetooth-only — every 'just use the Pixoo HTTP API' tutorial is,
   for us, a beautiful lie. Pixel control rides a serial channel — RFCOMM **channel
   2** — on the **same** device as the audio. We found it measurement-first; the real
   latency numbers are in FINDINGS.md. The protocol builder is byte-identical to the
   reference implementation and unit-tested. Three tiny Swift helpers for native
   Bluetooth / audio routing / mic; everything else is stdlib Python so the crab
   stays hackable."*

### Act 7 — Close (≈20 s) · runner
- **Screen:** a final confetti → idle → wave.
- **Say:** *"Clawd. He blinks, he ships, he judges your code, and he's open source.
  Be nice to him — he's doing his best."*

---

## Backup / failure plan
- BT drops → daemon auto-reconnects; the runner's `[r]` re-fires the last cue.
- Voice doesn't land → check Ditoo volume / routed output; banners carry the message
  visually too.
- Live Act 2 misbehaves → hit `[f]` for the scripted coding sequence.

## The runner
`clawd demo --show` — one act per keypress, the narration printed as a teleprompter,
each act's triggers fired on cue (driving the daemon directly). `[f]` = Act 2
scripted fallback, `[r]` = re-fire last, `[q]` = quit + reset.
