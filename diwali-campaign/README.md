# Diwali Campaign Film (20 s, 9:16)

A rebuilt, premium Diwali campaign cut for Kinekit Studio, exported to KineMaster. Open `Diwali_Campaign_9x16.recipe.json` in this folder's `Kinekit_Studio.html` (Chrome or Edge). The video clips are packed inside the recipe and load on their own.

- **Preview:** `preview/Diwali_Campaign_preview.mp4`, with the temp music.
- **Music:** the same temp Beatsync track as before. It's still loaded in your Studio; it isn't packed into the recipe.

## Art direction

- **Palette:** deep black, warm graded footage, one gold.
  - Every photo and clip gets the same grade: a little density, warm shadows and highlights, gentle contrast, slightly calmer colour.
  - On top: a subtle warm balance, fine grain and a soft vignette.
- **Typography:** Cinzel (classical inscription capitals) and Cormorant Garamond, rendered as engraved gold or cream with a real drop shadow and only a faint warm bloom. The Hindi line uses Tiro Devanagari: "शुभ दीपावली".
- **Fixed hierarchy:**
  - Titles are centred above a lotus divider.
  - Kinetic words always sit in the lower third, over a soft scrim, with the divider under them.
  - The tagline builds in one line instead of flashing.
- **Composition:**
  - Full-frame shots alternate with framed cards: the shot at 83% size with a hairline gold frame and corner ticks, floating on a soft shadow over a blurred, darker plate of the same footage.
  - One split layout uses two photo panels with a gold hairline between them.
- **Light, used sparingly:** your lens flare as the dissolve on act changes, one anamorphic streak per act, and real fireworks (from your video) composited in Screen blend for the final burst. No neon glow and no shakes.
- **Depth:** a slow camera push in the intro, the title and the finale. Layers sit at different depths (strings, mandala, plates, particles), so they move against each other.

## Your elements, reworked

| Supplied | What it became |
|---|---|
| Purple lotus line-art | recoloured to radial gold with a soft bloom, centre opened up; a slow-turning mandala behind the intro diya and the DIWALI title, at low opacity and set deep for parallax |
| Dotted ring | recoloured gold; the halo around the diya flame, turning slowly |
| Gold string with lotus | hanging strings that drop in at different depths (intro, finale); its lotus became the **divider** under every title |
| Diya bowl (no flame) | the **custom lit diya**: your bowl, a drawn realistic flame (blue root, white core) that flickers, warm light and a floor shadow; it ignites at the start and is the last light after the fade |
| Lens flare | flare dissolves on the act changes, the ignition flash, the sweep across DIWALI and the final burst |
| Particle videos | bokeh behind the intro and the hero, the particle ring behind DIWALI, dust over the people section |

## Timeline (cuts on the beat: 72.8 BPM, beat 0.8215 s)

| Time | Act |
|---|---|
| 0.00 – 2.97 | **Ignition.** Darkness with bokeh. Gold strings drop in at different depths and the lotus mandala fades up deep behind. The diya flame catches at 0.87 with a flare, and the dotted halo appears. **THIS DIWALI** opens from a strip, above a lotus divider. The camera pushes in slowly. |
| 2.97 – 6.26 | **Rituals.** A flare dissolve into the diya macro clip. Then a split layout: rangoli and diya-on-rangoli panels slide in from opposite sides with a gold hairline between them. Then the thali clip, the diya ring as a framed card over its blurred plate, and a slow dissolve to the hands lighting diyas with a light streak. |
| 6.26 – 9.54 | **People.** The women with candles as a framed card, then the thali (tilak), then the sparkler. **LIGHT**, **LOVE** and **CELEBRATE** each land on a beat in the lower third. The last shot speeds up into the title. |
| 9.54 – 12.83 | **Title.** A flare dissolve and sweep over the fireworks sky. **DIWALI** rises letter by letter inside the particle ring, with the gold mandala behind it. A divider and **FESTIVAL OF LIGHTS** follow. The camera pushes in. |
| 12.83 – 16.11 | **Montage.** Eight half-beat cuts mixing full frame and framed cards: fireworks, diya macro, women, thali, diya ring, city, sparkler, anaar. **LIGHT • JOY • TOGETHERNESS** builds word by word on the beats. |
| 16.11 – 20.00 | **Finale.** The field of diyas with strings in depth. **HAPPY**, then **DIWALI**, a divider and **शुभ दीपावली**. Real fireworks burst on the last beat (18.58). It fades to black at 19.0 and the lit diya with its halo stays. |

## Replacing footage

Picture and clip layers carry slot labels (Template tab), for example `Clip: diya ring` or `Photo: field of diyas (hero)`.
- **Photos:** use **Upload photo…**.
- **Clips:** import yours and drop them on the same time range, or use **Replace** in KineMaster after export.
- **Framed cards:** each card has a matching blurred plate layer. Replace both with the same clip, or create the plate with the `ffmpeg` line in `tools/premium_assets.py`.

## Rebuilding

```bash
pip install pillow numpy
npm pack @fontsource/cinzel @fontsource/cormorant-garamond @fontsource/tiro-devanagari-hindi   # then untar into FONTS_DIR
python3 tools/premium_assets.py IMAGES_DIR FONTS_DIR CLIPS_DIR PHOTOS_DIR assets   # supplied art 11-15, cut clips, 9:16 photos
python3 tools/build_premium.py assets tools/template.recipe.json Diwali_Campaign_9x16.recipe.json
```

All timing, placement and motion is in `tools/build_premium.py`, which reads one act after another. `CLIPS_DIR` and `PHOTOS_DIR` are `diwali-montage/media/clips` and `diwali-montage/media/photos`.
