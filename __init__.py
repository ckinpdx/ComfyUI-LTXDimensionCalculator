from .nodes import LTXDimensionCalculator, LTXFrameCalculator

NODE_CLASS_MAPPINGS = {
    "LTXDimensionCalculator": LTXDimensionCalculator,
    "LTXFrameCalculator":     LTXFrameCalculator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXDimensionCalculator": "LTX Dimension Calculator",
    "LTXFrameCalculator":     "LTX Frame Calculator",
}

WEB_DIRECTORY = "./web/js"
