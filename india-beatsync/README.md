# India Beat Sync (9:16)

A fast "dynamic promo" style beat-sync edit with an Indian theme, built for Kinekit Studio and exported to KineMaster.

- **Look:** one huge word per beat on rich gradients (saffron, rani pink, peacock, turmeric, indigo, maroon, green, cream, night).
- **Cuts:** hard cuts to full-frame pictures with a slow push-in.
- **Set pieces:** echo word stacks, a 4-tile collage, a 3-strip split panel and a tricolour brush-stroke wipe.
- **Stickers:** all drawn for this edit: marigold toran, diya, Ashoka chakra, gulal bursts, kites, rangoli, paisley, lotus, mandalas and a "Horn OK Please" truck-art plate.

## What's in the folder

| Path | What it is |
|---|---|
| `India_Beat_Sync_9x16.recipe.json` | The recipe. Open it in Kinekit Studio (File › Open, or drop it on the window). |
| `Kinekit_Studio.html` | Patched Studio. It has the corner-pin fix from the car edit, and saving a recipe now keeps stickers transparent (PNG). |
| `preview/India_Beat_Sync_preview.mp4` | Preview rendered from the Studio, with the music. |
| `music/Beatsync_edit_from_1m39s.m4a` | The track (72.8 BPM). |
| `assets/backgrounds/` | 9 gradient backgrounds, 1080×1920. |
| `assets/stickers/` | 26 transparent PNG stickers. |
| `assets/scenes/` | 9 illustrated picture cards, 1080×1920. These stand in for stock photos (see below). |
| `tools/` | Scripts that rebuild everything (see below). |

## Timeline (cuts on the beat grid: beat 0.8215 s, first beat 0.506 s)

The intro is soft. After that, every bar has three shots:
1. on the downbeat (with a chromatic-zoom hit),
2. on the syncopated accent 0.58 s later,
3. on the half beat at +1.23 s.

| Time | Shot 1 (downbeat) | Shot 2 | Shot 3 |
|---|---|---|---|
| 0.00 | Mandala opens like an iris | NAMASTE (0.51) | INDIA + marigold toran drops in (1.33), then tricolour wipe + BHARAT (2.15) |
| 2.97 | Holi picture + gulal bursts | RANGEELA | DESI echo stack |
| 4.61 | Taj Mahal picture | SHAAN | Collage: kites, fort, chai, diwali |
| 6.26 | Kites picture, kites flying | UDAAN | The music's break: HORN OK PLEASE |
| 7.90 | Rajasthan fort, big hit | SHAHI + paisleys | DHOOM echo stack |
| 9.54 | Chai picture | CHAI on cream | Split panel: Banaras, monsoon, cricket |
| 11.19 | Banaras ghats + diya | MASALA + rangoli | BAARISH monsoon picture |
| 12.83 | Cricket picture: SIXER! | JUNOON + chakra | JALWA echo stack |
| 14.47 | Diwali picture | ROSHNI + diya | DIL SE + lotus |
| 16.11 | Finale: tricolour flag, JAI HIND!, INCREDIBLE INDIA, marigolds. Fade to black at 18.0. | | |

A HUD frame overlay, film grain and a vignette run the whole way, like the reference.

## Pictures: swapping in Pexels / Pixabay photos

Pexels and Pixabay were blocked by this session's network policy, so every picture slot uses an illustrated stand-in. Each slot is labelled in the Studio with what to search for, for example `Photo: holi (pexels: holi festival colours india)`.

There are two ways to use real photos.

**In the Studio:** select the picture layer, then click **Upload photo…** in its panel and pick your stock image. All picture and word slots are listed in the **Template** tab.

**Automatically, with a free API key:**

```bash
PEXELS_API_KEY=xxxx python3 tools/fetch_stock.py        # or PIXABAY_API_KEY=xxxx
python3 tools/build_india.py assets tools/template.recipe.json tools/widths.json India_Beat_Sync_9x16.recipe.json
```

`fetch_stock.py` downloads the best portrait match for each scene, crops it to 9:16, keeps the illustration as `<name>.illustration.jpg`, and prints photographer credits.

For video clips: import them in the Studio's Media pane, then put a clip on a picture slot's time range.

## Rebuilding

```bash
pip install pillow numpy
python3 tools/assets.py assets            # redraw backgrounds, stickers and scenes
python3 tools/build_india.py assets tools/template.recipe.json tools/widths.json India_Beat_Sync_9x16.recipe.json
python3 tools/beats.py                    # beat analysis of music.wav (ffmpeg -i music/*.m4a -ac 1 -ar 22050 music.wav)
```

To re-time or re-word the edit, edit the shot list at the bottom of `tools/build_india.py`. The word sizes come from `tools/widths.json`, which holds Bebas Neue widths measured in the Studio. A new word needs a width entry first.
