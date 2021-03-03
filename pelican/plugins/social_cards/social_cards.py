"""
pelican.plugins.social_cards
===================================

Plugin to generate social media cards with post title embedded
"""

import html
import logging
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont
from pelican.generators import ArticlesGenerator, StaticGenerator
from smartypants import smartypants

from pelican import signals

from .settings import PLUGIN_SETTINGS, populate_plugin_settings

logger = logging.getLogger(__name__)

# FIXME: constants should be settings

LEADING = 15

# FIXME: better API:
# - CANVAS_WIDTH - preferred canvas width
# - CANVAS_HEIGHT - prefeered canvas height
# - CANVAS_LEFT - distance from left border to canvas left border
# - CANVAS_TOP - distance from top border to canvas top border

CANVAS_HORIZONTAL_MARGIN = 40
CANVAS_WIDTH = 1200 - CANVAS_HORIZONTAL_MARGIN * 2
CANVAS_HEIGHT = 382
CANVAS_TOP_MARGIN = 630 - CANVAS_HEIGHT


class TextBox:
    def __init__(self, text, font):
        self._text = text
        self._font = font
        self.width = 0
        self.height = 0
        self.lines = 0
        self.line_height = 0
        self.line_dimensions = {}

        self._compute_values()

    def _compute_values(self):
        max_width = 0
        max_height = 0

        for line in self._text:
            font_width, font_height = self._font.getsize(line)
            self.line_dimensions[line] = {
                "width": font_width,
                "height": font_height,
            }
            max_width = max(font_width, max_width)
            max_height = max(font_height, max_height)
        self.width = max_width
        self.line_height = max_height + LEADING
        self.lines = len(self._text)
        self.height = self.line_height * self.lines - LEADING


def is_plugin_configured():
    return PLUGIN_SETTINGS.get("configured", False)


def should_skip_object(content_object):
    return hasattr(content_object, PLUGIN_SETTINGS["KEY_NAME"])


def get_article_title(article):
    metadata_title = getattr(article, f"{PLUGIN_SETTINGS['KEY_NAME']}_text", None)
    if metadata_title:
        return metadata_title.split("\\n")

    # FIXME: rewrite this part, don't re-read file
    if not article.settings.get("TYPOGRIFY"):
        title = article.metadata.get("title")
    else:
        with open(article.source_path, encoding="UTF-8") as fh:
            for line in fh:
                if line.lower().startswith("title:"):
                    _, title = line.split(":", 1)
                    break
    title = html.unescape(smartypants(title.strip()))
    title = textwrap.wrap(
        title, width=30
    )  # FIXME: we need smarter way, that would use rendered font width
    return title


def create_paths_map(staticfiles):
    return {
        static_file.source_path: static_file.save_as
        for static_file in staticfiles
        if Path(static_file.source_path).is_relative_to(PLUGIN_SETTINGS["PATH"])
    }


def generate_thumbnail_image(template, text, output_path, context):
    font = context["image_font"]
    font_fill = context["FONT_FILL"]

    draw = ImageDraw.Draw(template)
    text_box = TextBox(text, font)

    # FIXME: different vertical and horizontal alignments
    # FIXME: warning, if text_box sizes are bigger than canvas

    current_y = ((CANVAS_HEIGHT - text_box.height) // 2) + CANVAS_TOP_MARGIN
    for line in text:
        current_x = (
            (CANVAS_WIDTH - text_box.line_dimensions[line]["width"]) // 2
        ) + CANVAS_HORIZONTAL_MARGIN
        if current_x < 0:
            logger.error(f"calculated negative x margin for '{line}', resetting to 0")
            current_x = 0
        draw.text((current_x, current_y), line, font=font, fill=font_fill)
        current_y += text_box.line_height
    template.save(output_path)


def generate_thumbnail_for_object(content_object, context):
    article_title = get_article_title(content_object)

    thumbnail_stem = (
        content_object.save_as.replace("/index.html", "").replace("/", "-").strip("-")
    )
    thumbnail_name = f"{thumbnail_stem}.png"
    thumbnail_path = context["PATH"] / thumbnail_name

    setattr(
        content_object,
        f"{PLUGIN_SETTINGS['KEY_NAME']}_source",
        thumbnail_path.as_posix(),
    )

    if (
        thumbnail_path.exists()
    ):  # FIXME: we might need a way to force overwriting anyway
        logger.debug(f"Refusing to overwrite existing {thumbnail_path}")
        return

    template = context["image_template"].copy()

    generate_thumbnail_image(template, article_title, thumbnail_path, context)


def generate_thumbnails(article_generator):
    if not is_plugin_configured():
        return

    PLUGIN_SETTINGS["PATH"].mkdir(exist_ok=True)

    template = Image.open(PLUGIN_SETTINGS["TEMPLATE"])
    image_font = ImageFont.truetype(
        PLUGIN_SETTINGS["FONT_FILENAME"], size=PLUGIN_SETTINGS["FONT_SIZE"]
    )

    additional_context = {"image_template": template, "image_font": image_font}

    context = {**PLUGIN_SETTINGS, **additional_context}

    for article in article_generator.articles:
        if should_skip_object(article):
            continue
        generate_thumbnail_for_object(article, context)


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
    signals.article_generator_finalized.connect(generate_thumbnails)
    signals.all_generators_finalized.connect(attach_metadata)
