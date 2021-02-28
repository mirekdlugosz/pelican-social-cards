'''
generate_social_thumbnails
===================================

Plugin to generate social media thumbnails with post title embedded
'''

import html
import logging
import textwrap
from pathlib import Path

from pelican import signals
from PIL import Image, ImageDraw, ImageFont
from smartypants import smartypants


logger = logging.getLogger(__name__)

LEADING = 15

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
                'width': font_width,
                'height': font_height,
            }
            max_width = max(font_width, max_width)
            max_height = max(font_height, max_height)
        self.width = max_width
        self.line_height = max_height + LEADING
        self.lines = len(self._text)
        self.height = self.line_height * self.lines - LEADING


def get_plugin_settings(pelican_settings):
    content_path = Path(pelican_settings.get('PATH'))
    SOCIAL_THUMBS_PATH = pelican_settings.get('SOCIAL_THUMBS_PATH', 'social-thumbs/')
    SOCIAL_THUMBS_PATH = content_path / SOCIAL_THUMBS_PATH
    SOCIAL_THUMBS_TEMPLATE = pelican_settings.get('SOCIAL_THUMBS_TEMPLATE')
    SOCIAL_THUMBS_FONT_FILENAME = pelican_settings.get('SOCIAL_THUMBS_FONT_FILENAME', "Arial.ttf")
    SOCIAL_THUMBS_FONT_SIZE = pelican_settings.get('SOCIAL_THUMBS_FONT_SIZE', "70")
    SOCIAL_THUMBS_FONT_FILL = pelican_settings.get('SOCIAL_THUMBS_FONT_FILL', "#000000")

    try:
        SOCIAL_THUMBS_FONT_SIZE = int(SOCIAL_THUMBS_FONT_SIZE)
    except ValueError:
        logger.error("SOCIAL_THUMBS_FONT_SIZE must be a number")

    return {
        'TEMPLATE': SOCIAL_THUMBS_TEMPLATE,
        'PATH': SOCIAL_THUMBS_PATH,
        'FONT_FILENAME': SOCIAL_THUMBS_FONT_FILENAME,
        'FONT_SIZE': SOCIAL_THUMBS_FONT_SIZE,
        'FONT_FILL': SOCIAL_THUMBS_FONT_FILL,
    }


def get_article_title(article):
    # FIXME: if user set "some" kind of metadata field, just use that - possibly after split
    if not article.settings.get('TYPOGRIFY'):
        title = article.metadata.get('title')
    else:
        with open(article.source_path, encoding="UTF-8") as fh:
            for line in fh:
                if line.lower().startswith("title:"):
                    _, title = line.split(':', 1)
                    break
    return html.unescape(smartypants(title.strip()))


def generate_thumbnail(template, text, output_path, context):
    font = context['image_font']
    font_fill = context['FONT_FILL']

    draw = ImageDraw.Draw(template)
    text_box = TextBox(text, font)

    current_y = ((CANVAS_HEIGHT - text_box.height) // 2) + CANVAS_TOP_MARGIN
    for line in text:
        current_x = ((CANVAS_WIDTH - text_box.line_dimensions[line]['width']) // 2) + CANVAS_HORIZONTAL_MARGIN
        if current_x < 0:
            logger.error(f"calculated negative x margin for '{line}', resetting to 0")
            current_x = 0
        draw.text((current_x, current_y), line, font=font, fill=font_fill)
        current_y += text_box.line_height
    template.save(output_path)


def process_article(content_object, context):
    article_title = get_article_title(content_object)
    wrapped_title = textwrap.wrap(article_title, width=30)  # FIXME: we need smarter way, that would use rendered font width

    thumbnail_stem = content_object.save_as.replace('/index.html', '').replace('/', '-').strip('-')
    thumbnail_name = f"{thumbnail_stem}.png"
    thumbnail_path = context['PATH'] / thumbnail_name

    if thumbnail_path.exists():  # FIXME: we might need a way to force overwriting anyway
        logger.debug(f"Refusing to overwrite existing {thumbnail_path}")
        return

    template = context['image_template'].copy()

    generate_thumbnail(template, wrapped_title, thumbnail_path, context)


def run_plugin(article_generator):
    plugin_settings = get_plugin_settings(article_generator.settings)

    plugin_settings['PATH'].mkdir(exist_ok=True)

    if not plugin_settings['TEMPLATE']:
        logger.error("Setting SOCIAL_THUMBS_TEMPLATE must be set")
        return

    template = Image.open(plugin_settings['TEMPLATE'])
    image_font = ImageFont.truetype("DejaVuSans.ttf", size=plugin_settings['FONT_SIZE'])

    additional_context = {
        'image_template': template,
        'image_font': image_font
    }

    context = {**plugin_settings, **additional_context}

    for article in article_generator.articles:
        process_article(article, context)


def register():
    signals.article_generator_finalized.connect(run_plugin)
