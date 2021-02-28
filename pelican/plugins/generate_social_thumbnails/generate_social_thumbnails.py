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

FONT_SIZE = 70
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


def generate_thumbnail(template, text, font, output_path):
    draw = ImageDraw.Draw(template)
    text_box = TextBox(text, font)

    current_y = ((CANVAS_HEIGHT - text_box.height) // 2) + CANVAS_TOP_MARGIN
    for line in text:
        current_x = ((CANVAS_WIDTH - text_box.line_dimensions[line]['width']) // 2) + CANVAS_HORIZONTAL_MARGIN
        if current_x < 0:
            logger.error(f"calculated negative x margin for '{line}', resetting to 0")
            current_x = 0
        draw.text((current_x, current_y), line, font=font, fill="#212529")
        current_y += text_box.line_height
    template.save(output_path)


def process_article(content_object, context):
    template = context['SOCIAL_THUMBS_TEMPLATE'].copy()

    article_title = get_article_title(content_object)
    wrapped_title = textwrap.wrap(article_title, width=30)  # FIXME: we need smarter way, that would use rendered font width

    thumbnail_stem = content_object.save_as.replace('/index.html', '').replace('/', '-').strip('-')
    thumbnail_name = f"{thumbnail_stem}.png"
    thumbnail_path = context['SOCIAL_THUMBS_PATH'] / thumbnail_name

    if thumbnail_path.exists():  # FIXME: we might need a way to force overwriting anyway
        logger.debug(f"Refusing to overwrite existing {thumbnail_path}")
        return

    generate_thumbnail(template, wrapped_title, context['FONT'], thumbnail_path)


def run_plugin(article_generator):
    CONTENT_PATH = Path(article_generator.settings.get('PATH'))
    SOCIAL_THUMBS_TEMPLATE = article_generator.settings.get('SOCIAL_THUMBS_TEMPLATE')
    SOCIAL_THUMBS_PATH = article_generator.settings.get('SOCIAL_THUMBS_PATH', 'social-thumbs/')
    SOCIAL_THUMBS_PATH = CONTENT_PATH / SOCIAL_THUMBS_PATH

    SOCIAL_THUMBS_PATH.mkdir(exist_ok=True)

    if not SOCIAL_THUMBS_TEMPLATE:
        logger.error("Setting SOCIAL_THUMBS_TEMPLATE must be set")
        return

    template = Image.open(SOCIAL_THUMBS_TEMPLATE)
    template.convert("RGBA")
    font = ImageFont.truetype("DejaVuSans.ttf", size=FONT_SIZE)

    context = {
        'SOCIAL_THUMBS_PATH': SOCIAL_THUMBS_PATH,
        'SOCIAL_THUMBS_TEMPLATE': template,
        'FONT': font,
    }

    for article in article_generator.articles:
        process_article(article, context)


def register():
    signals.article_generator_finalized.connect(run_plugin)
