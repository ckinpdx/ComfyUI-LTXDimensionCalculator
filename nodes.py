from math import gcd

try:
    from server import PromptServer
    from aiohttp import web
    _HAS_SERVER = True
except ImportError:
    _HAS_SERVER = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRID         = 64
TOLERANCE    = 0.03       # ±3% ratio deviation
LANDSCAPE_MAX = 3776      # last multiple of 64 before 3840 (4K)
PORTRAIT_MAX_H = 1920
PORTRAIT_MAX_W = 1088
SHORT_MIN    = 512

# ---------------------------------------------------------------------------
# Ratio definitions  (long, short, landscape label, portrait label)
# ---------------------------------------------------------------------------
RATIOS = [
    (16,  9, "16:9 — YouTube, HD, TV",      "9:16 — TikTok, Reels, Shorts"),
    (21,  9, "21:9 — Ultrawide, cinematic", "9:21 — Ultrawide portrait"),
    ( 4,  3, "4:3 — Classic TV, monitor",   "3:4 — Tablet portrait"),
    ( 3,  2, "3:2 — Photography, DSLR",     "2:3 — Portrait photo"),
    ( 2,  1, "2:1 — Cinematic wide",        "1:2 — Tall mobile"),
    ( 5,  4, "5:4 — Old CRT monitor",       "4:5 — Instagram portrait"),
    ( 1,  1, "1:1 — Square, Instagram",     "1:1 — Square, Instagram"),
]

# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------
def _build_options(ratio_long: int, ratio_short: int, landscape: bool) -> list:
    """
    Return sorted list of 'WxH' strings for the given aspect ratio + orientation.
    ratio_long >= ratio_short (the long-edge to short-edge ratio).
    """
    target    = ratio_long / max(ratio_short, 1)
    max_long  = LANDSCAPE_MAX  if landscape else PORTRAIT_MAX_H
    max_short = LANDSCAPE_MAX  if landscape else PORTRAIT_MAX_W
    max_a     = max_long // GRID

    candidates = {}  # (long_px, short_px) → deviation

    for a in range(1, max_a + 1):
        long_px = a * GRID
        for b in range(1, a + 1):       # b <= a  →  short <= long
            short_px = b * GRID
            if short_px > max_short:
                break                   # inner loop only grows; no point continuing
            if short_px < SHORT_MIN:
                continue
            dev = abs((long_px / short_px) - target) / target
            if dev <= TOLERANCE:
                candidates[(long_px, short_px)] = dev

    if not candidates:
        return []

    # Cull: shared long dimension → keep lower deviation
    by_long = {}
    for (l, s), dev in candidates.items():
        if l not in by_long or dev < by_long[l][1]:
            by_long[l] = ((l, s), dev)

    # Cull: shared short dimension → keep lower deviation
    by_short = {}
    for (l, s), dev in by_long.values():
        if s not in by_short or dev < by_short[s][1]:
            by_short[s] = ((l, s), dev)

    ordered = sorted(by_short.values(), key=lambda x: x[0][0] * x[0][1])
    result = [f"{l}x{s}" if landscape else f"{s}x{l}" for (l, s), _ in ordered]

    # Cap square options to the same count as the largest non-square list
    if ratio_long == ratio_short and _SQUARE_CAP is not None and len(result) > _SQUARE_CAP:
        result = _trim_evenly(result, _SQUARE_CAP)

    return result


def _trim_evenly(lst: list, n: int) -> list:
    """Return n evenly-spaced elements from lst, always including first and last."""
    indices = sorted({round(i * (len(lst) - 1) / (n - 1)) for i in range(n)})
    return [lst[i] for i in indices]


# Compute square cap from the largest non-square option list across all ratios/orientations
_SQUARE_CAP = None
_SQUARE_CAP = max(
    (len(_build_options(rl, rs, land))
     for rl, rs, *_ in RATIOS if rl != rs
     for land in (True, False)),
    default=15,
)

# Default options for initial widget state (16:9 landscape)
_DEFAULT_OPTS = _build_options(16, 9, landscape=True)

# Master lists for server-side validation — must include every value the JS can set.
# ComfyUI validates saved workflow values against INPUT_TYPES at prompt time.
_ALL_RATIO_LABELS = (
    [ls for _, _, ls, _ in RATIOS] +
    [pt for _, _, _, pt in RATIOS if pt not in [ls for _, _, ls, _ in RATIOS]]
)

_all_res: set = set()
for _rl, _rs, *_ in RATIOS:
    _g = gcd(_rl, _rs)
    _rln, _rsn = max(_rl // _g, _rs // _g), min(_rl // _g, _rs // _g)
    _all_res.update(_build_options(_rln, _rsn, landscape=True))
    _all_res.update(_build_options(_rln, _rsn, landscape=False))
_ALL_RESOLUTIONS = sorted(_all_res, key=lambda s: int(s.split("x")[0]) * int(s.split("x")[1]))


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------
class LTXDimensionCalculator:
    CATEGORY = "LTX"

    @classmethod
    def INPUT_TYPES(cls):
        mid = len(_DEFAULT_OPTS) // 2
        return {
            "required": {
                "ratio":        (_ALL_RATIO_LABELS, {
                    "default": _ALL_RATIO_LABELS[0],
                    "tooltip": "Common aspect ratios and their typical applications.",
                }),
                "orientation":  (["Landscape", "Portrait"], {
                    "default": "Landscape",
                    "tooltip": "Switches between landscape and portrait resolution lists. Portrait is capped at 1088×1920.",
                }),
                "resolution":   (_ALL_RESOLUTIONS, {
                    "default": _DEFAULT_OPTS[mid],
                    "tooltip": "All options are divisible by 64 (LTX-compatible). List updates when ratio or orientation changes.",
                }),
            }
        }

    RETURN_TYPES  = ("INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES  = ("width", "height", "width_half", "height_half", "label")
    FUNCTION      = "calculate"

    def calculate(self, ratio: str, orientation: str, resolution: str):
        w, h = map(int, resolution.split("x"))
        return (w, h, w // 2, h // 2, resolution)


# ---------------------------------------------------------------------------
# LTX Frame Calculator
# ---------------------------------------------------------------------------
class LTXFrameCalculator:
    CATEGORY = "LTX"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seconds": ("FLOAT", {
                    "default": 5.0, "min": 0.1, "max": 300.0, "step": 0.1,
                    "tooltip": "Desired clip duration in seconds.",
                }),
                "fps": ("FLOAT", {
                    "default": 24.0, "min": 1.0, "max": 120.0, "step": 1.0,
                    "tooltip": "Frames per second. LTX reference is 24 fps.",
                }),
            }
        }

    RETURN_TYPES  = ("INT", "FLOAT")
    RETURN_NAMES  = ("frame_count", "actual_seconds")
    FUNCTION      = "calculate"

    def calculate(self, seconds: float, fps: float):
        raw = seconds * fps
        # Snap to nearest valid LTX frame count: (frames - 1) % 8 == 0, minimum 9
        n = max(1, round((raw - 1) / 8))
        frames = 8 * n + 1
        actual = frames / fps
        return (frames, round(actual, 4))


# ---------------------------------------------------------------------------
# API endpoint — called by the JS extension to populate the resolution widget
# ---------------------------------------------------------------------------
if _HAS_SERVER:
    @PromptServer.instance.routes.get("/ltx-dim-calc/resolutions")
    async def _get_resolutions(request):
        ratio_str   = request.rel_url.query.get("ratio", "16:9")
        orientation = request.rel_url.query.get("orientation", "Landscape")
        landscape   = orientation == "Landscape"

        try:
            rw, rh = map(int, ratio_str.split(":"))
        except (ValueError, IndexError):
            return web.json_response([])

        g  = gcd(rw, rh)
        rw, rh = rw // g, rh // g
        ratio_long  = max(rw, rh)
        ratio_short = min(rw, rh)

        return web.json_response(_build_options(ratio_long, ratio_short, landscape))
