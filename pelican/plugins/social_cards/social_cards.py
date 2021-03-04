"""
pelican.plugins.social_cards
===================================

Plugin to generate social media cards with post title embedded
"""

import logging
from pathlib import Path

from pelican.generators import ArticlesGenerator, StaticGenerator

from pelican import signals

from .cards_generator import CardsGenerator
from .settings import PLUGIN_SETTINGS, populate_plugin_settings

logger = logging.getLogger(__name__)


def is_plugin_configured():
    return PLUGIN_SETTINGS.get("configured", False)


def should_skip_object(content_object):
    return hasattr(content_object, PLUGIN_SETTINGS["KEY_NAME"])


def create_paths_map(staticfiles):
    return {
        static_file.source_path: static_file.save_as
        for static_file in staticfiles
        if Path(static_file.source_path).is_relative_to(PLUGIN_SETTINGS["PATH"])
    }


def generate_cards(generator):
    if not is_plugin_configured():
        return

    PLUGIN_SETTINGS["PATH"].mkdir(exist_ok=True)

    cards_generator = CardsGenerator()

    # FIXME: drafts, translations, pages...
    for article in generator.articles:
        if should_skip_object(article):
            continue
        cards_generator.create_for_object(article)


def attach_metadata(finished_generators):
    if not is_plugin_configured():
        return

    for generator in finished_generators:
        if isinstance(generator, ArticlesGenerator):
            articles_generator = generator
        if isinstance(generator, StaticGenerator):
            static_generator = generator

    thumb_paths_map = create_paths_map(static_generator.staticfiles)

    # FIXME: drafts, translations, pages...
    for article in articles_generator.articles:
        if should_skip_object(article):
            continue

        key = getattr(article, f"{PLUGIN_SETTINGS['KEY_NAME']}_source")
        value = thumb_paths_map.get(key)
        if not key or not value:
            continue
        # FIXME: appending SITEURL should be configurable - some themes add that on their own, some do not
        # something like THUMB_URL = '{siteurl}/{value}', with these two keys being recognized
        # value = f"{PLUGIN_SETTINGS['SITEURL']}/{value}"
        setattr(article, PLUGIN_SETTINGS["KEY_NAME"], value)


def register():
    signals.initialized.connect(populate_plugin_settings)
    signals.article_generator_finalized.connect(generate_cards)
    signals.all_generators_finalized.connect(attach_metadata)
