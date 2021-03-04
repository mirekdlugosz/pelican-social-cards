"""
pelican.plugins.social_cards
===================================

Plugin to generate social media cards with post title embedded
"""

import itertools
import logging
from pathlib import Path

from pelican.generators import ArticlesGenerator, PagesGenerator, StaticGenerator

from pelican import signals

from .cards_generator import CardsGenerator
from .settings import PLUGIN_SETTINGS, populate_plugin_settings

logger = logging.getLogger(__name__)


def is_plugin_configured():
    return PLUGIN_SETTINGS.get("configured", False)


def should_skip_object(content_object):
    return hasattr(content_object, PLUGIN_SETTINGS["KEY_NAME"])


def generator_content(generator):
    content_sources = ["articles", "translations", "pages"]
    if PLUGIN_SETTINGS["INCLUDE_DRAFTS"]:
        content_sources.extend(
            ("drafts", "drafts_translations", "draft_pages", "drafts_translations")
        )
    if PLUGIN_SETTINGS["INCLUDE_HIDDEN"]:
        content_sources.extend(("hidden_pages", "hidden_translations"))

    all_content = [
        getattr(generator, source_name, []) for source_name in content_sources
    ]

    for content_object in itertools.chain(*all_content):
        yield content_object


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

    for content_object in generator_content(generator):
        if should_skip_object(content_object):
            continue
        cards_generator.create_for_object(content_object)


def attach_metadata(finished_generators):
    if not is_plugin_configured():
        return

    for generator in finished_generators:
        if isinstance(generator, ArticlesGenerator):
            articles_generator = generator
        if isinstance(generator, PagesGenerator):
            pages_generator = generator
        if isinstance(generator, StaticGenerator):
            static_generator = generator

    thumb_paths_map = create_paths_map(static_generator.staticfiles)

    for content_object in itertools.chain(
        *(generator_content(articles_generator), generator_content(pages_generator))
    ):
        if should_skip_object(content_object):
            continue

        key = getattr(content_object, f"{PLUGIN_SETTINGS['KEY_NAME']}_source")
        value = thumb_paths_map.get(key)
        if not key or not value:
            continue
        # FIXME: appending SITEURL should be configurable - some themes add that on their own, some do not
        # something like THUMB_URL = '{siteurl}/{value}', with these two keys being recognized
        # value = f"{PLUGIN_SETTINGS['SITEURL']}/{value}"
        setattr(content_object, PLUGIN_SETTINGS["KEY_NAME"], value)


def register():
    signals.initialized.connect(populate_plugin_settings)
    signals.article_generator_finalized.connect(generate_cards)
    signals.page_generator_finalized.connect(generate_cards)
    signals.all_generators_finalized.connect(attach_metadata)
