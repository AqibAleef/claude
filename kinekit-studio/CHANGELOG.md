# Kinekit Studio: changes made in this repo

The latest Studio is always `Kinekit_Studio.html` in this folder. The copies inside each project folder are the same file.

## Offset mode: re-transform without adding keys (Shift+O)

A layer can carry an **offset** (move X / Y / depth, rotation, scale, 3D tilt) that sits on top of its whole animation.

- **Turning it on:** press **Shift+O**, pick **Offset all keys** in Object › Transform › Edits, or use Object menu › Offset mode. A cyan **OFFSET MODE** tag shows in the viewport while it's on.
- **What changes:** G / R / S in the viewport, the rotate and scale handles, and every Transform field now shift the whole animation. Every key keeps its timing and easing, no key is added or changed, and the key diamonds are hidden.
- **Turning it off:** Shift+O again. Edits key the transform at the playhead as before, and the offset stays applied on top. Keys are written without the offset, so it is never counted twice.
- **Panel controls:** the panel lists the current offset. **Bake into keys** writes it into every key (or the still layer) and clears it, so the motion looks identical. **Reset offset** removes it.
- **Saving and export:** recipes save the offset (`xo`). The KineMaster export bakes it into the exported keyframes as usual.

## Origin: pivot point for rotation and scale (Shift+P)

Each layer has an **origin**: the point its rotation and scale turn around. By default it's the layer centre.

- **Panel:** in Object › Origin, set **Origin X / Y** (px from the layer centre), or click one of the **9 snap buttons** (corners, edge midpoints, centre).
- **Viewport:** **Shift+P** (or **Move in viewport**) moves the origin with the mouse. It snaps to the layer's edges and centre; hold Ctrl for free placement and X / Y to lock an axis. A blue crosshair shows the origin on the selected layer.
- **Keep the layer in place** (on by default): moving the origin doesn't make the layer jump at the playhead. The compensation goes into the layer's offset, never its keys. Turn it off to let the layer move with its new pivot.
- **Behaviour:** it applies to keyed rotation and scale, the offset, and R / S in the viewport. With no rotation and 100% scale the origin never changes where a layer sits. 3D tilt still turns around the layer centre.
- **Saving and export:** recipes save the origin (`org`). The KineMaster export bakes it into the exported keyframes.

## Earlier patches

- **Corner-pin layers:** the base transform is fitted to the true screen shape, which removes the 0.1 s warps in KineMaster.
- **Recipe images:** saving a recipe keeps transparent images (stickers) as PNG.
- **Recipe clips:** recipes can carry their video clips (`studio_videos`). They load on open and are packed again on Save recipe.

`patches/03_offset_and_origin.py` reapplies the offset and origin change to an older Studio file: `python3 03_offset_and_origin.py OLD.html NEW.html`.
