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
}


def get_plugin_settings(pelican_settings=None):
    if PLUGIN_SETTINGS:
        return PLUGIN_SETTINGS

    for key, default_value in DEFAULT_SETTINGS.items():
        value = pelican_settings.get(f'SOCIAL_THUMBS_{key}', default_value)
        PLUGIN_SETTINGS[key] = value

    if not PLUGIN_SETTINGS.get('TEMPLATE'):
        logger.error(
            "Setting SOCIAL_THUMBS_TEMPLATE must be set for "
            "pelican-generate-social-thumbnails to work"
        )

    content_path = Path(pelican_settings.get('PATH'))
    PLUGIN_SETTINGS['PATH'] = content_path / PLUGIN_SETTINGS['PATH']

    try:
        PLUGIN_SETTINGS['FONT_SIZE'] = int(PLUGIN_SETTINGS['FONT_SIZE'])
    except ValueError:
        logger.error("SOCIAL_THUMBS_FONT_SIZE must be a number")

    PLUGIN_SETTINGS['SITEURL'] = pelican_settings.get('SITEURL', '').rstrip('/')
    PLUGIN_SETTINGS['configured'] = True

    return PLUGIN_SETTINGS
