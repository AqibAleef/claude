# DRIVEN 146: photo montage cut to the music (22.74 s, 9:16)

This edit uses the music from **1:39 to the end** of `Beatsync_edit_2026_10_07_23_33_54.mp4`. Every cut, camera step, band landing, whip, flash and fade is placed on the beat map below, measured from that audio.

Open `DRIVEN_146_Montage_9x16.recipe.json` in this folder's `Kinekit_Studio.html` (Chrome or Edge). Then add the 1:39–end audio as the music; it starts at 0:00 of the timeline. (It's the same audio as the `Beatsync_edit_from_1m39s` track already in your Studio.)

- **Preview:** `preview/DRIVEN_146_preview.mp4`, 30 fps with the music.
- **Contents:** photos only (16–20 and sharp crops of them), no video clips.

## What the music does (measured)

The analysis used librosa onset detection per frequency band (808/kick, snare, clap, hats), then fitted a grid to the hats (fit R = 0.76). Scripts: `tools/onsets.py`, `tools/fit_grid.py`, `tools/bar_map.py`.

- **Tempo:** **146 BPM**. One eighth note = **0.20546 s**; the grid starts at 0.0496 s.
- **Groove:** every bar has the same **3-3-2** pattern.
  - **Slot 0:** 808 + clap (the strongest hit).
  - **Slot 3:** clap.
  - **Slot 5:** 808.
  - **Slot 7:** a pickup kick in most bars.

| Time (s) | Section | What the music does |
|---|---|---|
| 0.04 / 0.26 | Intro hit | a double hit, then quiet |
| 0.46 – 1.28 | Quiet | sparse soft hits |
| 1.28 – 2.93 | Build bar | snare roll and rising hats |
| **2.926** | **DROP** | the groove starts (bar 0) |
| 4.57 / 6.21 / 7.86 | Bars 1–3 | groove; bar 3 has a fill on slots 6–7 |
| **9.501** | **Phrase 2** | the energy peaks again (bar 4) |
| 11.14 / 12.79 / 14.43 | Bars 5–7 | the densest bars; fills at the ends of bars 5 and 6 |
| 15.46 – 16.07 | Break | the bass cuts out; a clap at 15.87 |
| **16.075** | **FINAL HIT** | then a decaying tail; silent by about 20.5 s |

## How the picture follows it

| Time | Picture |
|---|---|
| 0.04 | A sharp tail-light band cuts in from black on the first hit and punches on the second; a red rule draws. |
| 0.46 | On the clap: the rain-on-glass shot with a slow, smooth push (the quiet part gets the longest hold). |
| 1.28 – 2.93 | Build: the race in 2.5D with an accelerating push. Cuts tighten with the snare roll (crowd, kerb). The last shot speed-ramps into the drop with a building impact zoom. |
| **2.93 drop** | Flash, shake and impact zoom. The Ferrari card lands with a scale punch. The camera *steps* forward on the 3 and the 5, a rule draws on the 3, and a light streak passes on the 5. |
| 4.57 | The convertible and crowd in 2.5D, with the camera stepping on 3 and 5. The pickup on 7 whips it out. |
| 6.01 → 6.21 | The rally card whips in on the pickup and lands exactly on the downbeat. |
| 7.86 | **Triptych:** one band lands on each hit of the 3-3-2. The fill steps them sideways, and the pickup throws them out. |
| **9.50 phrase 2** | A big hit: a pull-out reveal of the race (the camera starts close and pulls back). Then a cut on the 3 (crowd) and on the 5 (the rally card, tight). |
| 10.94 – 12.58 | Three shots per bar: a rotation punch on the 3, a zoomed 2.5D hit on the 5, and a whip on every pickup. |
| 12.58 – 14.43 | Fastest: a cut on every accent (7, 0, 1, 3, 5, 7). |
| 14.43 | **Triptych reprise**, faster (0, 2, 3). |
| 15.46 | In the break, the bands hang and drift apart. On the clap (15.87), the middle band is sucked in with a speed ramp. |
| **16.08 final hit** | The Ferrari hero. **DRIVEN** lands on the tail's next 808 (16.69) and **BY INSTINCT** on 17.31. A slow pull-out runs while the music rings out; the picture fades by 20.4, the title by 21.4, then black to the end. |

## Keeping the photos sharp

- **No over-enlarging:** no photo is shown much bigger than its native size.
  - **Portrait photos** (17, 18, 19) and their crops fill the frame at no more than 1.1× enlargement.
  - **Landscape photos** (16, 20) are too small to fill a 9:16 frame sharply, so they're shown as wide **cards** that bleed off the sides over their own blurred backdrop.
- **Depth:** the car always sits on its own cut-out layer, a little nearer the camera, so every camera move separates it from its background.

## KineMaster

- **Ready-made export:** `DRIVEN_146_9x16.kine`, exported with the fixed Studio (patch 05).
- **Angle keys:**
  - Only the 8 layers with a deliberate tilt punch carry Angle keys, e.g. −3° → 0° on the 3 of bar 5.
  - Camera shakes are position-only, so they add no Angle keys.
  - There are 0 jumps between 0° and 360°.
- **Opacity:** constant on every layer.
- **Band slide-ins:** the keyframe check flags them, but they're fast one-way ease-out arrivals that land on the hit, not glitches.

## Rebuilding

```
python3 tools/car_prep.py PHOTOS CUTOUTS CLIPS FONTS assets     # plates, cut-outs, type
python3 tools/car_prep2.py PHOTOS assets CUTOUTS                # sharp crops, bands, cards
python3 tools/build_driven2.py assets tools/template.recipe.json DRIVEN_146_Montage_9x16.recipe.json
```
