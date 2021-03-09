import logging
from pathlib import Path
import textwrap

logger = logging.getLogger(__name__)

PLUGIN_SETTINGS = {}

DEFAULT_SETTINGS = {
    "TEMPLATE": None,
    "PATH": "social-cards/",
    "FORMAT_EXTENSION": "png",
    "FONT_FILENAME": "Arial.ttf",
    "FONT_SIZE": 70,
    "FONT_FILL": "#000000",
    "FONT_OUTLINE_SIZE": 0,
    "FONT_OUTLINE_FILL": "#000000",
    "CANVAS_WIDTH": 1200,
    "CANVAS_HEIGHT": 630,
    "CANVAS_LEFT": 0,
    "CANVAS_TOP": 0,
    "HORIZONTAL_ALIGNMENT": "center",
    "VERTICAL_ALIGNMENT": "center",
    "LEADING": 15,
    "WRAPPING_FUNCTION": textwrap.wrap,
    "CHARS_PER_LINE": 30,
    "KEY_NAME": "og_image",
    "INCLUDE_SITEURL": False,
    "INCLUDE_DRAFTS": False,
    "INCLUDE_HIDDEN": False,
    "FORCE_SAVE": False,
    "configured": False,
}

MANDATORY_SETTINGS = ["TEMPLATE"]
VALID_ALIGNMENTS = {
    "VERTICAL": ("top", "center", "bottom"),
    "HORIZONTAL": ("left", "center", "right"),
}


def populate_plugin_settings(pelican_instance):
    for key, default_value in DEFAULT_SETTINGS.items():
        value = pelican_instance.settings.get(f"SOCIAL_CARDS_{key}", default_value)
        PLUGIN_SETTINGS[key] = value

    missing_settings = [
        f"SOCIAL_CARDS_{key}"
        for key in MANDATORY_SETTINGS
        if not PLUGIN_SETTINGS.get(key)
    ]

    if missing_settings:
        logger.error(
            "Following settings must be set for pelican.plugins.social_cards "
            "to work: {}".format(", ".join(missing_settings))
        )
        return

    PLUGIN_SETTINGS["configured"] = True

    content_path = Path(pelican_instance.settings.get("PATH"))
    PLUGIN_SETTINGS["PATH"] = content_path / PLUGIN_SETTINGS["PATH"]

    int_settings = [
        key for key, value in DEFAULT_SETTINGS.items() if isinstance(value, int)
    ]
    for key in int_settings:
        try:
            PLUGIN_SETTINGS[key] = int(PLUGIN_SETTINGS[key])
        except ValueError:
            logger.error(f"SOCIAL_CARDS_{key} must be a number")

    for key in ("VERTICAL", "HORIZONTAL"):
        valid_values = VALID_ALIGNMENTS.get(key)
        if PLUGIN_SETTINGS[f"{key}_ALIGNMENT"] not in valid_values:
            logger.error(
                f"SOCIAL_CARDS_{key}_ALIGNMENT must be one of: "
                f"{', '.join(valid_values)}"
            )
            default_value = DEFAULT_SETTINGS.get(f"{key}_ALIGNMENT")
            PLUGIN_SETTINGS[f"{key}_ALIGNMENT"] = default_value

    logger.debug(f"pelican.plugins.social_cards settings: {PLUGIN_SETTINGS}")
