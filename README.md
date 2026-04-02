# ComfyUI LTX Dimension Calculator

A ComfyUI custom node that calculates valid dimensions for [LTX-Video](https://github.com/Lightricks/LTX-Video) generation. All output dimensions are divisible by 64, ensuring compatibility with LTX's VAE and the first-stage latent in two-stage pipelines.

## Features

- **Common aspect ratios** — 16:9, 21:9, 4:3, 3:2, 2:1, 5:4, 1:1
- **Portrait / Landscape toggle** — switches the resolution list and updates use-case labels (e.g. *YouTube, HD, TV* ↔ *TikTok, Reels, Shorts*)
- **Dynamic resolution dropdown** — options update automatically when ratio or orientation changes; all entries are within ±3% of the target ratio and divisible by 64
- **Landscape range** — up to 3776px on the long edge (just under 4K)
- **Portrait cap** — 1088×1920 max
- **Half-resolution toggle** — outputs `width ÷ 2` and `height ÷ 2` for use as the first-stage latent size in two-stage workflows, without changing the displayed label

## Node

**Category:** `LTX`
**Display name:** LTX Dimension Calculator

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `ratio` | Combo | Aspect ratio with common use-case label |
| `orientation` | Combo | Landscape or Portrait |
| `resolution` | Combo | Valid div-by-64 resolution for the selected ratio and orientation |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `width` | INT | Full width in pixels |
| `height` | INT | Full height in pixels |
| `width_half` | INT | Half width — for first-stage latent size in two-stage workflows |
| `height_half` | INT | Half height — for first-stage latent size in two-stage workflows |
| `label` | STRING | Resolution string as displayed (e.g. `1088x1920`) |

## Installation

### Via ComfyUI Manager
Search for **LTX Dimension Calculator** in the Install Custom Nodes dialog.

### Manual
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ckinpdx/ComfyUI-LTXDimensionCalculator
```

No additional dependencies required.

## How dimensions are chosen

For each aspect ratio, all `(a×64) × (b×64)` pairs within the resolution bounds are enumerated. Pairs within ±3% of the target ratio are kept. Where two candidates share a dimension, the one closer to the target ratio is preferred. The resulting list is sorted by area.

For the 1:1 square ratio the list is capped to the same length as the largest non-square ratio list, with entries spread evenly across the full resolution range.
