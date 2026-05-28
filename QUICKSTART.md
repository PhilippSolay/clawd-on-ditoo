# Clawd on Ditoo — Quickstart (Ditoo Pro)

From zero to a clapping, chirping pixel crab in five steps.

## 1. Pair the Ditoo

System Settings → Bluetooth → connect **`DitooPro-Audio`**. That one device does
both audio *and* pixels — there is no separate "-Light" device.

## 2. Grant Bluetooth + find your MAC

```bash
cd /Users/philippsolay/code/divoom-pet
./bench/discover.sh
```

Click **Allow**. Note the MAC (the Pro here is `AA:BB:CC:DD:EE:FF`) and that the
pixel channel is **RFCOMM 2**.

## 3. Grant Microphone (for claps)

```bash
./ditoo_ears/DitooEars.app/Contents/MacOS/DitooEars
```

Click **Allow**, clap once (you'll see `clap …`), then Ctrl-C. Uses your MacBook
mic, so the Ditoo's audio stays full quality.

## 4. Bring Clawd to life

```bash
./bin/clawd start --foreground --mac AA:BB:CC:DD:EE:FF -v
```

He hatches (asterisk → crab) with a wake chirp + "Hi! I'm Clawd", from the
Ditoo's speaker. Your music stays on whatever output you've selected.

Now play:
- 👏 **clap** → poke (startle + heart + bip)
- 👏👏 **double-clap fast** → sleep / wake toggle
- wait ~90s → he yawns and naps

**Ctrl-C** to stop.

To see every mood, start it in the **background** instead and run the demo:

```bash
./bin/clawd start --mac AA:BB:CC:DD:EE:FF && sleep 3 && ./bin/clawd demo
./bin/clawd stop      # when done
```

## 5. Wire him to your coding

```bash
./bin/clawd install-hooks
```

Patches `~/.claude/settings.json` (backed up first). From your next Claude Code
session, Clawd reacts to real work: thinks when Claude thinks, gears on tool
calls, hearts when done, frets on errors.

## If something's off

```bash
./bin/clawd doctor          # checks devices, binaries, voices, daemon
./bin/clawd sounds preview  # audition the chirps + spoken lines
tail -f ~/.clawd/daemon.log # live daemon log (background mode)
```

- Sounds coming from the wrong speaker? Clawd routes to a device whose name
  contains "DitooPro" by default — override with `--audio-device "Name"`.
- Claps too touchy / too deaf? `--clap-floor` (default 0.06) and `--clap-rise`
  (default 4.0) on `clawd start`.
