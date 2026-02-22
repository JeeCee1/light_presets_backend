DOMAIN = "light_presets"

STORAGE_VERSION = 1
STORAGE_KEY = "light_presets"

# Preset types - named to match light.turn_on attribute names exactly
PRESET_TYPE_COLOR_TEMP_KELVIN = "color_temp_kelvin"
PRESET_TYPE_RGB = "rgb"
PRESET_TYPE_HS = "hs"
PRESET_TYPE_BRIGHTNESS_ONLY = "brightness_only"

PRESET_TYPES = [
    PRESET_TYPE_COLOR_TEMP_KELVIN,
    PRESET_TYPE_RGB,
    PRESET_TYPE_HS,
    PRESET_TYPE_BRIGHTNESS_ONLY,
]

# Service names - match rgb-light-card naming convention
SERVICE_APPLY_COLOR = "applyColor"
SERVICE_GET_PRESETS = "get_presets"
SERVICE_SAVE_PRESET = "save_preset"
SERVICE_DELETE_PRESET = "delete_preset"
SERVICE_SAVE_CATEGORY = "save_category"
SERVICE_DELETE_CATEGORY = "delete_category"

# Default category
DEFAULT_CATEGORY_NAME = "Default"
