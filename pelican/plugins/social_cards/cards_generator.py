import html
import logging

from PIL import Image, ImageDraw, ImageFont

from .settings import PLUGIN_SETTINGS

logger = logging.getLogger(__name__)

TYPOGRIFY_SPAN_CLASSES = ("amp", "caps", "dquo", "quo")


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
        leading = PLUGIN_SETTINGS["LEADING"]
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
        self.line_height = max_height + leading
        self.lines = len(self._text)
        self.height = self.line_height * self.lines - leading


class CardsGenerator:
    _font = None
    _template = None

    def __init__(self):
        if not self._font:
            type(self)._font = ImageFont.truetype(
                PLUGIN_SETTINGS["FONT_FILENAME"], size=PLUGIN_SETTINGS["FONT_SIZE"]
            )

        if not self._template:
            type(self)._template = Image.open(PLUGIN_SETTINGS["TEMPLATE"])

    def _get_article_title(self, article):
        metadata_title = getattr(article, f"{PLUGIN_SETTINGS['KEY_NAME']}_text", None)
        if metadata_title:
            return metadata_title.split("\\n")

        wrapping_function = PLUGIN_SETTINGS["WRAPPING_FUNCTION"]

        title = article.metadata.get("title", "")
        if article.settings.get("TYPOGRIFY"):
            for class_name in TYPOGRIFY_SPAN_CLASSES:
                title = title.replace(f'<span class="{class_name}">', "")
            title = title.replace("</span>", "")
            title = html.unescape(title)

        title = wrapping_function(
            title.strip(), width=PLUGIN_SETTINGS["CHARS_PER_LINE"]
        )
        return title

    def _get_card_path(self, content_object):
        card_stem = content_object.save_as.replace("/", "-")

        bad_suffixes = ("-index.html", ".html")
        for bad_suffix in bad_suffixes:
            if card_stem.endswith(bad_suffix):
                trim = len(bad_suffix) * -1
                card_stem = card_stem[:trim]
        card_stem = card_stem.strip("-")

        card_name = f"{card_stem}.png"
        card_path = PLUGIN_SETTINGS["PATH"] / card_name
        return card_path

    def _generate_card_image(self, text):
        img = self._template.copy()
        draw = ImageDraw.Draw(img)
        text_box = TextBox(text, self._font)
        font_fill = PLUGIN_SETTINGS["FONT_FILL"]
        canvas_width = PLUGIN_SETTINGS["CANVAS_WIDTH"]
        canvas_height = PLUGIN_SETTINGS["CANVAS_HEIGHT"]
        canvas_left = PLUGIN_SETTINGS["CANVAS_LEFT"]
        canvas_top = PLUGIN_SETTINGS["CANVAS_TOP"]

        # FIXME: different vertical and horizontal alignments
        # FIXME: warning, if text_box sizes are bigger than canvas
        current_y = ((canvas_height - text_box.height) // 2) + canvas_top
        for line in text:
            current_x = (
                (canvas_width - text_box.line_dimensions[line]["width"]) // 2
            ) + canvas_left
            if current_x < 0:
                logger.error(
                    f"calculated negative x margin for '{line}', resetting to 0"
                )
                current_x = 0
            draw.text((current_x, current_y), line, font=self._font, fill=font_fill)
            current_y += text_box.line_height
        return img

    def create_for_object(self, content_object):
        target_path = self._get_card_path(content_object)

        attr_name = f"{PLUGIN_SETTINGS['KEY_NAME']}_source"
        setattr(content_object, attr_name, target_path.as_posix())

        # FIXME: we might need a way to force overwriting anyway
        if target_path.exists():
            logger.debug(f"Refusing to overwrite existing {target_path}")
            return

        article_title = self._get_article_title(content_object)

        img = self._generate_card_image(article_title)
        img.save(target_path)
