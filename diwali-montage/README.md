# Diwali Montage (20 s, 9:16)

A premium, beat-synced Diwali montage for Instagram Reels, built in Kinekit Studio and exported to KineMaster.

- **Look:** deep blacks, warm gold, amber and saffron. Light-based effects only, no cartoon art.
- **Footage:** every shot is a numbered **placeholder card** that says what to drop in. Replace them with your clips and photos.
- **Ready as is:** the typography, light effects, camera moves, transitions and timing are final.

## Files

| Path | What it is |
|---|---|
| `Diwali_Montage_9x16.recipe.json` | The recipe. Open it in Kinekit Studio (File › Open, or drop it on the window). |
| `Kinekit_Studio.html` | Patched Studio (same patches as the India edit). |
| `preview/Diwali_Montage_preview.mp4` | Preview rendered from the Studio, with the temp music. |
| `assets/holders/` | 20 placeholder cards (1080×1920). |
| `assets/vfx/` | Transparent light elements: 3 gold particle depth layers, diya flame, bloom, anamorphic streak, gold sweep, 3 firework bursts, 2 firework trails, gold line mandala, gold dust burst, gold rule. |
| `tools/` | `diwali_assets.py` redraws the elements and cards; `build_diwali.py` builds the recipe. |

## Timeline

The cuts sit on the music's grid: 72.8 BPM, beat 0.8215 s, first beat 0.506 s. The drop lands at 2.97 s, which matches the brief's "0:03 beat hit".

| Time | What happens |
|---|---|
| 0.00 – 2.97 | **Darkness**, with gold particles drifting in 3 depth layers. At 0.87 the **diya flame ignites** with a bloom and the diya shot fades up. The camera pushes slowly toward the flame. **THIS DIWALI** opens from a thin strip, with a gold light streak running along its edge, then a gold rule appears. |
| 2.97 – 6.26 | **Rapid montage**: diya, rangoli, marigolds, sweets, decorations, then a slower shot of hands lighting diyas. Transitions used: flash frame, gold dust burst, impact zoom and shake on the drop; whip pans with motion blur; a match cut (the zoom carries across the cut); speed-ramp push-ins; and a light streak into the slow shot. |
| 6.26 – 9.54 | **People / gifts / celebration.** **LIGHT**, **LOVE** and **CELEBRATE** each land on a beat, with a punch-in overshoot, motion blur and camera shake. The last shot speeds up into the sweep. |
| 9.54 – 12.83 | **The reveal.** A gold light sweep with a flash and impact shake. **DIWALI** assembles letter by letter from scattered particles, with subtle 3D depth and a glow. A gold line mandala turns behind it, two firework trails orbit the title, and firework bursts land on the next three beats. *FESTIVAL OF LIGHTS* fades up under a gold rule. The camera pushes slowly in. |
| 12.83 – 16.11 | **Fastest section**: eight cuts, one every half beat. A rotating mandala, particles and two light streaks run over the footage. Flash frames and shakes hit both bar downbeats. LIGHT, then JOY, then TOGETHERNESS flash in small text, followed by **LIGHT • JOY • TOGETHERNESS**. |
| 16.11 – 20.00 | **Hero shot** with a slow camera push. **HAPPY** and then **DIWALI** rise in letter by letter in gold, with a gold rule and a light streak. On the final beat (18.58) fireworks explode behind the text, with a bloom and a shake. At 19.0 the scene fades to black and **one small diya keeps glowing**. |

A warm grade, film grain and a vignette sit over everything.

## Footage slots

| Time (s) | Slot |
|---|---|
| 0.87 – 2.97 | Video 01: Diya close-up in darkness (macro, flame catches) |
| 2.97 – 3.38 | Video 02: Diya flame, tight |
| 3.38 – 3.79 | Video 03: Rangoli top-down |
| 3.79 – 4.20 | Photo 04: Marigold flowers |
| 4.20 – 4.61 | Photo 05: Mithai / sweets |
| 4.61 – 5.19 | Video 06: Festive decorations, fairy-light bokeh |
| 5.19 – 6.26 | Video 07: Hands lighting diyas (the slow, emotional shot) |
| 6.26 – 7.08 | Video 08: People in traditional clothing |
| 7.08 – 7.90 | Video 09: Exchanging gifts |
| 7.90 – 9.54 | Video 10: Family celebrating, sparklers (two layers: hold + speed ramp; use the same clip for both) |
| 9.54 – 12.83 | Video 11: Night bokeh behind DIWALI (shown at 55% so the title glows) |
| 12.83 – 16.11 | Video 12 fireworks, 13 diya rows, 14 family, Photo 15 sweets, Photo 16 rangoli, Video 17 city lights, 18 smiling faces, 19 fireworks / anaar (0.41 s each) |
| 16.11 – 19.95 | Video 20: Hero, a Diwali night scene with diyas and fireworks behind |

**How to replace them:**
- **Photos:** select the holder layer in the Studio and click **Upload photo…**. Its push, whip and ramp keyframes stay.
- **Videos:** export to KineMaster first, then use **Replace** on each holder layer there. Alternatively, import the clip in the Studio's Media pane, put it on the same time range, and delete the holder.
- **Speed ramps:** for a real speed ramp, set the clip speed in KineMaster. The push keyframes already ramp the motion.

## Real-footage version

`Diwali_Montage_9x16_REAL.recipe.json` is the same edit, cut from your video, your 5 photos and elements from your zip. **Its clips are packed inside the recipe file.** Open it in the patched `Kinekit_Studio.html` and they load on their own. When you export, KineMaster gets real video layers with the right trims.

- **Browser:** use Chrome or Edge. Their MP4 (H.264) playback is what the Studio needs; some other browsers can't play these clips.
- **Re-saving:** File › Save recipe keeps the clips inside the file.
- **Preview:** `preview/Diwali_Montage_real_preview.mp4`, with the temp music.

| Shot | Footage |
|---|---|
| 01 ignition | photo: diya in the dark (flame bloom on the real flame) |
| 02, 13 | clip `diya_macro` (diya flame macro) |
| 03 | photo: marigold rangoli with diyas |
| 04 | photo: diya on colour rangoli |
| 05, 09 (LOVE), 15 | clip `thali` (girl with puja thali) |
| 06, 16 | clip `diya_ring` (top-down ring of diyas) |
| 07 slow shot | photo: hands lighting diyas |
| 08 (LIGHT), 14 | clip `women` (two women in sarees with candles) |
| 10 (CELEBRATE), 18 | clip `sparkler_woman` |
| 11 behind DIWALI | clip `sky_wide` (fireworks over the horizon) |
| 12 | clip `fw_purple` |
| 17 | clip `sky_city` |
| 19 | clip `anaar` (fountain) |
| 20 hero | photo: field of diyas (soft scrim behind HAPPY DIWALI) |

**Elements from the zip:**
- **Diya:** stray specks removed. It's the diya left glowing at the end.
- **Rangoli:** soft-masked into a medallion that turns under DIWALI.
- **Lantern:** baked backdrop keyed out, then mirrored for the two hanging lanterns in the hero shot.
- **Not used:** `fireworks.png` and `golden_particle_trail.png` have their beige background baked in, and `happy_diwali_title.png` is cut off ("HAPPY DIWA"). The drawn light elements cover these instead.

`media/` holds the prepared clips (720×1280 MP4), the 9:16 photo crops and the cleaned elements. To re-cut from the source files:

```bash
python3 tools/media_prep.py 1008.mp4 PHOTOS_DIR ELEMENTS_DIR media      # photos named 1.jpg..5.jpg as sent
python3 tools/build_diwali_real.py assets media tools/template.recipe.json tools/dw_widths.json Diwali_Montage_9x16_REAL.recipe.json
```

To change which part of the source video a clip uses, edit `CLIPS` in `media_prep.py`. The slot-to-footage map is `MEDIA_FOR` in `build_diwali_real.py`.

## Sound

The music is the **temp track** from the India edit (`Beatsync_edit_from_1m39s.m4a`), already loaded in your Studio. Its drop matches the brief at 0:03. To use a different festive track, swap it, then re-time by changing `BPM` / `OFF` at the top of `tools/build_diwali.py` and rebuilding.

These KineMaster sounds are already attached in the recipe:
- Woosh on the whips and streaks
- Smokey on the flame ignition and the particle titles
- Pop on LIGHT / LOVE / CELEBRATE

The brief's other sounds aren't in the Studio's sound list. Add them in KineMaster (Audio › Sound Effects) at these times:

| Time (s) | Sound |
|---|---|
| 0.87 | Diya ignition / match strike |
| 1.53 | Soft bell + shimmer (THIS DIWALI) |
| 2.97 | Big impact + riser end (drop) |
| 4.61, 7.90, 9.54, 12.83, 14.47 | Impact hits |
| 9.54 | Whoosh + sparkle swell (gold sweep) |
| 10.36, 11.19, 12.01 | Firework pops |
| 12.83 – 16.11 | Sparkle ticks on cuts |
| 18.58 | Firework explosion (big) |
| 19.0 – 20.0 | Bell tail as it fades to black |

## Rebuilding

```bash
pip install pillow numpy
python3 tools/diwali_assets.py assets
python3 tools/build_diwali.py assets tools/template.recipe.json tools/dw_widths.json Diwali_Montage_9x16.recipe.json
```

The words live in `tools/build_diwali.py`. Each title's size comes from `tools/dw_widths.json` (Bebas Neue widths at the tracking used), so a new word needs a width entry first.
