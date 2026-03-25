"""Color palette matching the Penpot UI design mockup."""

from raylib import ffi as _ffi


def _color(r: int, g: int, b: int, a: int = 255):
    """Create a raylib Color struct."""
    return _ffi.new("Color *", [r, g, b, a])[0]


# Card header
HEADER_BG = _color(0, 121, 107)             # Teal
HEADER_TEXT = _color(255, 255, 255)          # White

# Card body
CARD_BG = _color(215, 215, 215)             # Light gray
CARD_BORDER = _color(80, 80, 80)            # Dark gray border
CARD_DIVIDER = _color(185, 185, 185)        # Section divider

# Ports
PORT_DOT = _color(33, 150, 243)             # Blue dots
PORT_TEXT = _color(50, 50, 50)              # Dark label text

# Canvas
CANVAS_BG = _color(158, 158, 158)           # Medium gray workspace

# Toolbar
TOOLBAR_BG = _color(200, 200, 200)          # Toolbar strip
TOOLBAR_BORDER = _color(160, 160, 160)      # Toolbar bottom edge

# Connections
CONNECTION_LINE = _color(40, 40, 40)         # Dark curve
CONNECTION_DOT = _color(40, 40, 40)          # Midpoint dot

# Tooltip (message inspector)
TOOLTIP_BG = _color(180, 180, 180, 200)      # Semi-transparent gray
TOOLTIP_BORDER = _color(80, 80, 80)          # Dashed border
TOOLTIP_TEXT = _color(40, 40, 40)            # Dark text

# Drag handle (6-dot grid in header)
DRAG_HANDLE = _color(0, 80, 68)             # Dark teal dots

# Selection highlight
SELECTION_OUTLINE = _color(156, 39, 176, 180) # Purple

# Play/pause button
BUTTON_BG = _color(190, 190, 190)
BUTTON_HOVER = _color(170, 170, 170)
BUTTON_ICON = _color(50, 50, 50)

# Footer
FOOTER_TEXT = _color(100, 100, 100)
