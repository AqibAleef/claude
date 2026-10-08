# DRIVEN — car beat-sync (18.6 s, 9:16)

A premium music-video edit built from your 5 photos (16–20) and 5 clips, for Kinekit Studio, exported to KineMaster.
Open `DRIVEN_Car_BeatSync_9x16.recipe.json` in this folder's `Kinekit_Studio.html` (Chrome or Edge). The clips are packed inside the recipe and load on their own.

- **Preview:** `preview/DRIVEN_preview.mp4` (30 fps, with your Beatsync track). Contact sheets are in `preview/`.
- **Music:** your "Beatsync_edit_from_1m39s" track, already in your Studio. It isn't packed into the recipe. Cuts are timed from the start of that track.

## How the depth works

Every photo with a car (16, 17, 19, 20) is two layers on the same pixel grid:
- **Back plate** (`bg_N.jpg`): the photo with the car region deeply defocused and a gentle lens blur, placed far back.
- **Car layer** (`fg_N.png`): a BiRefNet cut-out in front.

The scene camera pushes, pulls and drifts across both layers, so the car really separates from its background. That gives real parallax, not a flat zoom. Photo 18 (rain) and close crops (tail lights, wheels, racers, crowd, dust) are used as flat inserts.

## Beat grid

73 BPM: one beat every 0.8215 s, first beat at 0.506 s. Key moments: drop 2.97, break 7.49, **big hit 7.90**, peak 12.83–16.11, hero 16.11, **final hit 17.76**.

- **Strong beats get impact:** scale punch, a 2–3 frame micro-shake, a flash frame, a directional/zoom blur and a light streak.
- **Weak beats stay smooth:** camera drift and longer holds.
- **Energy builds:** two shots per bar, then three, then a cut every half beat, then the hero.

| Time | Section |
|---|---|
| 0.00 – 2.97 | **Hook.** Letterbox. Flash cuts on the kicks (tail lights, wheel, racers), then the ignition clip; **DRIVEN** slices in over a red rule. |
| 2.97 – 7.49 | **Build.** Chapter counter 01–03. Parallax push on the yellow racers (17) → wheels clip; lateral pan across the red car (16) → blue supercar clip; the Challenger (19) settles in. |
| 7.49 – 7.90 | **Break.** Bars close on the rain shot, **BUILT TO** holds. |
| 7.90 | **Big hit.** Flash, punch and shake into the rally car (20), with **MOVE**. |
| 7.90 – 12.83 | **Drive.** Tunnel clip at 1.8×, dust crop, Challenger clip, the racers zoomed, the red flank, then ignition at 1.6× and the crowd. Three shots per bar with whips and zoom blur. |
| 12.83 – 16.11 | **Peak.** A cut every half beat across all photos and clips, with alternating whip directions. |
| 16.11 – 17.76 | **Hero.** The red car (16) in a slow parallax push. **DRIVEN / BY INSTINCT** builds in the lower third. |
| 17.76 – 18.60 | **Final hit.** A clean cut to black on the last beat, the title held on black, a controlled fade out. |

## Look

- **Grade:** denser blacks, cool shadows, warm highlights; reds kept rich.
- **Finishing:** fine grain and a soft vignette.
- **Typography:** Anton for the big words and Syncopate (wide-tracked) for the small lines. White with soft shadows; red rules are the only accent colour.
- **Restraint:** no glitches and no neon.

## KineMaster

- **Export:** builds a 13 MB `.kine`, no errors.
- **Keyframes:** the keyframe-spike check found 0 spikes on all 82 baked layers.
- **Opacity:** constant on every layer, since KineMaster can't animate it.

## Tools

The `tools/` scripts rebuild everything:
- `car_prep.py`: plates, cut-outs, crops, graded clips and type.
- `build_car.py`: builds the timeline/recipe.
- `template.recipe.json`: the base layer template.

```
python3 tools/car_prep.py PHOTOS CUTOUTS CLIPS FONTS assets
python3 tools/build_car.py assets tools/template.recipe.json DRIVEN_Car_BeatSync_9x16.recipe.json
```
