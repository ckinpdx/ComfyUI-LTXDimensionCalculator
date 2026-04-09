from .nodes import LTXDimensionCalculator, LTXDimensionCalculator3Stage, LTXFrameCalculator

NODE_CLASS_MAPPINGS = {
    "LTXDimensionCalculator":        LTXDimensionCalculator,
    "LTXDimensionCalculator3Stage":  LTXDimensionCalculator3Stage,
    "LTXFrameCalculator":            LTXFrameCalculator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXDimensionCalculator":        "LTX Dimension Calculator",
    "LTXDimensionCalculator3Stage":  "LTX Dimension Calculator 3 Stage",
    "LTXFrameCalculator":            "LTX Frame Calculator",
}

WEB_DIRECTORY = "./web/js"
