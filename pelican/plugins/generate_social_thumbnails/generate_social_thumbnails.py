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


class TitleCard:
    def __init__(self, text, font):
        self.width = 0
        self.height = 0
        self.img = None
        self._text_img = None
        self._bg_img = None

        self._create_text_img(text, font)
        self._create_bg_img()
        self._create_final_img()

    def _create_text_img(self, text, font):
        LEADING = 20
        img = Image.new('RGBA', (1200, 630), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        text_params = {
            'text': "\n".join(text),
            'font': font,
            'spacing': LEADING,
        }
        self.width, self.height = draw.multiline_textsize(**text_params)
        self.height += LEADING
        draw.multiline_text((0, 0), align='center', fill='#000000', **text_params)
        self._text_img = img.crop((0, 0, self.width, self.height))
        self._text_img.save('/tmp/test-text-img.png')

    def _create_bg_img(self):
        w, h = self._text_img.size
        w += 40
        h += 40
        img = Image.new('RGBA', (w, h), (255, 255, 255, 235))
        img.paste(self._text_img, (20, 20), self._text_img)
        self._bg_img = img
        self._bg_img.save('/tmp/test-bg-img.png')

    def _create_final_img(self):
        img = Image.new('RGBA', (1200, 630), (0, 0, 0, 0))
        width, height = self._bg_img.size
        left = ((800 - width) // 2) + 200
        top = (630 - height) // 2

        img.paste(self._bg_img, (left, top), self._bg_img)
        self.img = img
        self.img.save('/tmp/test-final-img.png')


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


def generate_thumbnail(template, text, output_path):
    FONT_SIZE = 70
    MAX_W = 800
    IMG_H = 630
    MARGIN_LEFT = 200

    bg = Image.open(template)
    wrapped_text = textwrap.wrap(text, width=23)  # FIXME: we need smarter way, that would use rendered font width
    font = ImageFont.truetype("DejaVuSans.ttf", size=FONT_SIZE)
    title_card = TitleCard(wrapped_text, font)

    bg.convert("RGBA")
    bg = Image.alpha_composite(bg, title_card.img)

    bg.save(output_path)


def process_article(content_object):
    CONTENT_PATH = Path(content_object.settings.get('PATH'))
    SOCIAL_THUMBS_TEMPLATE = content_object.settings.get('SOCIAL_THUMBS_TEMPLATE')
    SOCIAL_THUMBS_PATH = content_object.settings.get('SOCIAL_THUMBS_PATH', 'social-thumbs/')
    SOCIAL_THUMBS_PATH = CONTENT_PATH / SOCIAL_THUMBS_PATH

    SOCIAL_THUMBS_PATH.mkdir(exist_ok=True)

    if not SOCIAL_THUMBS_TEMPLATE:
        logger.error("Setting SOCIAL_THUMBS_TEMPLATE must be set")
        return

    article_title = get_article_title(content_object)

    thumbnail_stem = content_object.save_as.replace('/index.html', '').replace('/', '-').strip('-')
    thumbnail_name = f"{thumbnail_stem}.png"
    thumbnail_path = SOCIAL_THUMBS_PATH / thumbnail_name

    if thumbnail_path.exists():  # FIXME: we might need a way to force overwriting anyway
        logger.debug(f"Refusing to overwrite existing {thumbnail_path}")
        return

    generate_thumbnail(SOCIAL_THUMBS_TEMPLATE, article_title, thumbnail_path)


def run_plugin(article_generator):
    for article in article_generator.articles:
        process_article(article)


def register():
    signals.article_generator_finalized.connect(run_plugin)
