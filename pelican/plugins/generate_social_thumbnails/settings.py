import logging
from pathlib import Path


logger = logging.getLogger(__name__)

PLUGIN_SETTINGS = {}

DEFAULT_SETTINGS = {
    "TEMPLATE": None,
    "PATH": "social-thumbs/",
    "FONT_FILENAME": "Arial.ttf",
    "FONT_SIZE": 70,
    "FONT_FILL": "#000000",
    "KEY_NAME": "og_image",
    "configured": False,
}

MANDATORY_SETTINGS = ['TEMPLATE']


def populate_plugin_settings(pelican_instance):
    for key, default_value in DEFAULT_SETTINGS.items():
        value = pelican_instance.settings.get(f'SOCIAL_THUMBS_{key}', default_value)
        PLUGIN_SETTINGS[key] = value

    missing_settings = [
        f"SOCIAL_THUMBS_{key}"
        for key in MANDATORY_SETTINGS
        if not PLUGIN_SETTINGS.get(key)
    ]

    if missing_settings:
        logger.error(
            "Following settings must be set for pelican-generate-social-thumbnails "
            "to work: {}".format(", ".join(missing_settings))
        )
        return

    PLUGIN_SETTINGS['configured'] = True

    content_path = Path(pelican_instance.settings.get('PATH'))
    PLUGIN_SETTINGS['PATH'] = content_path / PLUGIN_SETTINGS['PATH']

    try:
        PLUGIN_SETTINGS['FONT_SIZE'] = int(PLUGIN_SETTINGS['FONT_SIZE'])
    except ValueError:
        logger.error("SOCIAL_THUMBS_FONT_SIZE must be a number")

    logger.debug(f"pelican-generate-social-thumbnails settings: {PLUGIN_SETTINGS}")
