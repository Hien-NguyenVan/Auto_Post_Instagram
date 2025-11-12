"""
Windows 11 Style Theme for CustomTkinter
Modern, clean design with rounded corners
"""

# ==================== COLORS ====================
# Windows 11 Light Theme Colors
COLORS = {
    # Background colors
    "bg_primary": "#F3F3F3",      # Main background (light gray)
    "bg_secondary": "#FFFFFF",    # Card/Panel background (white)
    "bg_tertiary": "#FAFAFA",     # Subtle background

    # Accent colors (Windows 11 Blue)
    "accent": "#0078D4",          # Primary accent (Windows blue)
    "accent_hover": "#005A9E",    # Accent hover state
    "accent_pressed": "#004578",  # Accent pressed state

    # Text colors
    "text_primary": "#201F1E",    # Primary text (dark gray)
    "text_secondary": "#605E5C",  # Secondary text (medium gray)
    "text_tertiary": "#8A8886",   # Tertiary text (light gray)
    "text_on_accent": "#FFFFFF",  # Text on accent color

    # Status colors
    "success": "#10893E",         # Success green
    "success_hover": "#0B6A30",
    "warning": "#F7B500",         # Warning yellow
    "warning_hover": "#C89400",
    "danger": "#D13438",          # Danger red
    "danger_hover": "#A52A2D",
    "info": "#00BCF2",            # Info blue
    "info_hover": "#0099C6",

    # Border colors
    "border_light": "#E1DFDD",    # Light border
    "border_medium": "#D2D0CE",   # Medium border
    "border_dark": "#8A8886",     # Dark border

    # Surface colors
    "surface_1": "#FFFFFF",       # Elevated surface level 1
    "surface_2": "#F9F9F9",       # Elevated surface level 2
    "surface_3": "#F3F3F3",       # Elevated surface level 3

    # Interactive states
    "hover_overlay": "#00000008",  # Subtle hover overlay (5% black)
    "pressed_overlay": "#00000010", # Subtle pressed overlay (10% black)
    "disabled": "#A19F9D",        # Disabled state
    "disabled_bg": "#F3F3F3",     # Disabled background
}

# ==================== DIMENSIONS ====================
DIMENSIONS = {
    # Corner radius (Windows 11 style)
    "corner_radius_small": 4,     # Small elements (buttons)
    "corner_radius_medium": 8,    # Medium elements (cards, inputs)
    "corner_radius_large": 12,    # Large elements (panels, dialogs)

    # Border width
    "border_width_thin": 1,
    "border_width_medium": 2,
    "border_width_thick": 3,

    # Spacing
    "spacing_xs": 4,
    "spacing_sm": 8,
    "spacing_md": 12,
    "spacing_lg": 16,
    "spacing_xl": 24,
    "spacing_xxl": 32,

    # Button dimensions
    "button_height": 32,
    "button_padding_x": 16,
    "button_padding_y": 8,

    # Input dimensions
    "input_height": 32,
    "input_padding": 12,
}

# ==================== FONTS ====================
FONTS = {
    # Font family (Windows 11 uses Segoe UI Variable, fallback to Segoe UI)
    "family": "Segoe UI",
    "family_mono": "Consolas",

    # Font sizes
    "size_small": 11,
    "size_normal": 12,
    "size_medium": 14,
    "size_large": 16,
    "size_title": 20,
    "size_heading": 24,

    # Font weights
    "weight_normal": "normal",
    "weight_semibold": "bold",  # Tkinter only supports normal and bold
    "weight_bold": "bold",
}

# ==================== BUTTON STYLES ====================
BUTTON_STYLES = {
    "primary": {
        "fg_color": COLORS["accent"],
        "hover_color": COLORS["accent_hover"],
        "text_color": COLORS["text_on_accent"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": 0,
        "font": (FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
    },
    "success": {
        "fg_color": COLORS["success"],
        "hover_color": COLORS["success_hover"],
        "text_color": COLORS["text_on_accent"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": 0,
        "font": (FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
    },
    "warning": {
        "fg_color": COLORS["warning"],
        "hover_color": COLORS["warning_hover"],
        "text_color": COLORS["text_primary"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": 0,
        "font": (FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
    },
    "danger": {
        "fg_color": COLORS["danger"],
        "hover_color": COLORS["danger_hover"],
        "text_color": COLORS["text_on_accent"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": 0,
        "font": (FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
    },
    "secondary": {
        "fg_color": COLORS["bg_secondary"],
        "hover_color": COLORS["surface_2"],
        "text_color": COLORS["text_primary"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": DIMENSIONS["border_width_thin"],
        "border_color": COLORS["border_medium"],
        "font": (FONTS["family"], FONTS["size_normal"], FONTS["weight_normal"]),
    },
}

# ==================== FRAME STYLES ====================
FRAME_STYLES = {
    "panel": {
        "fg_color": COLORS["bg_secondary"],
        "corner_radius": DIMENSIONS["corner_radius_large"],
        "border_width": DIMENSIONS["border_width_thin"],
        "border_color": COLORS["border_light"],
    },
    "card": {
        "fg_color": COLORS["surface_1"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": 0,
    },
    "group": {
        "fg_color": COLORS["bg_tertiary"],
        "corner_radius": DIMENSIONS["corner_radius_medium"],
        "border_width": DIMENSIONS["border_width_thin"],
        "border_color": COLORS["border_light"],
    },
}

# ==================== CUSTOMTKINTER APPEARANCE ====================
def apply_ctk_theme():
    """Apply CustomTkinter theme settings"""
    import customtkinter as ctk

    # Set appearance mode (light/dark)
    ctk.set_appearance_mode("light")  # Windows 11 light theme

    # Set default color theme
    ctk.set_default_color_theme("blue")

    # Apply custom colors
    # Note: CustomTkinter uses theme files for comprehensive theming
    # For now, we'll apply colors individually to widgets

def get_button_style(style_name="primary"):
    """Get button style configuration"""
    return BUTTON_STYLES.get(style_name, BUTTON_STYLES["primary"])

def get_frame_style(style_name="panel"):
    """Get frame style configuration"""
    return FRAME_STYLES.get(style_name, FRAME_STYLES["panel"])
