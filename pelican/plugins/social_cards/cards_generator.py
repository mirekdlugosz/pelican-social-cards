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
        self._line_dimensions = {}

        self._compute_values()

    def _compute_values(self):
        leading = PLUGIN_SETTINGS["LEADING"]
        max_width = 0
        max_height = 0

        for line in self._text:
            font_width, font_height = self._font.getsize(line)
            self._line_dimensions[line] = {
                "width": font_width,
                "height": font_height,
            }
            max_width = max(font_width, max_width)
            max_height = max(font_height, max_height)
        self.width = max_width
        self.line_height = max_height + leading
        self.lines = len(self._text)
        self.height = self.line_height * self.lines - leading

    def width_of_line(self, line):
        return self._line_dimensions.get(line, {}).get("width", 0)


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
            self._check_canvas_position()

    def _check_canvas_position(self):
        template_w, template_h = self._template.size
        canvas_w = PLUGIN_SETTINGS["CANVAS_WIDTH"] + PLUGIN_SETTINGS["CANVAS_LEFT"]
        canvas_h = PLUGIN_SETTINGS["CANVAS_HEIGHT"] + PLUGIN_SETTINGS["CANVAS_TOP"]

        if canvas_w > template_w or canvas_h > template_h:
            logger.warning(
                (
                    "pelican.plugins.social_cards: Template size is {}x{}, "
                    "bottom right corner of canvas is at ({}, {})\n"
                    "Part of the text may be drawn outside of image borders."
                ).format(template_w, template_h, canvas_w, canvas_h)
            )

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

        card_name = f"{card_stem}.{PLUGIN_SETTINGS['FORMAT_EXTENSION']}"
        card_path = PLUGIN_SETTINGS["PATH"] / card_name
        return card_path

    def _calc_current_y(self, text_box):
        canvas_height = PLUGIN_SETTINGS["CANVAS_HEIGHT"]
        canvas_top = PLUGIN_SETTINGS["CANVAS_TOP"]
        vertical_alignment = PLUGIN_SETTINGS["VERTICAL_ALIGNMENT"]

        y = 0  # top
        if vertical_alignment != "top":
            y = canvas_height - text_box.height  # bottom
            if vertical_alignment == "center":
                y = y // 2
        y += canvas_top
        return y

    def _calc_current_x(self, text_box, line):
        canvas_width = PLUGIN_SETTINGS["CANVAS_WIDTH"]
        canvas_left = PLUGIN_SETTINGS["CANVAS_LEFT"]
        horizontal_alignment = PLUGIN_SETTINGS["HORIZONTAL_ALIGNMENT"]

        x = 0  # left
        if horizontal_alignment != "left":
            x = canvas_width - text_box.width_of_line(line)  # right
            if horizontal_alignment == "center":
                x = x // 2
        x += canvas_left
        return x

    def _generate_card_image(self, text):
        img = self._template.copy()
        draw = ImageDraw.Draw(img)
        text_box = TextBox(text, self._font)
        font_fill = PLUGIN_SETTINGS["FONT_FILL"]
        canvas_width = PLUGIN_SETTINGS["CANVAS_WIDTH"]
        canvas_height = PLUGIN_SETTINGS["CANVAS_HEIGHT"]
        outline_size = PLUGIN_SETTINGS["FONT_OUTLINE_SIZE"]
        outline_fill = PLUGIN_SETTINGS["FONT_OUTLINE_FILL"]

        if text_box.width > canvas_width or text_box.height > canvas_height:
            logger.warning(
                (
                    "pelican.plugins.social_cards: Text requires more space than "
                    "canvas provides\n"
                    "text dimensions: {}x{}; canvas dimensions: {}x{}\n"
                    "offending text: {}"
                ).format(
                    text_box.width,
                    text_box.height,
                    canvas_width,
                    canvas_height,
                    " ".join(text),
                )
            )

        current_y = self._calc_current_y(text_box)

        for line in text:
            current_x = self._calc_current_x(text_box, line)
            draw.text(
                (current_x, current_y),
                line,
                font=self._font,
                fill=font_fill,
                stroke_width=outline_size,
                stroke_fill=outline_fill,
            )
            current_y += text_box.line_height
        return img

    def create_for_object(self, content_object):
        logger.debug(
            f"pelican-social-cards: generating image for {content_object.source_path}"
        )

        target_path = self._get_card_path(content_object)

        attr_name = f"{PLUGIN_SETTINGS['KEY_NAME']}_source"
        setattr(content_object, attr_name, target_path.as_posix())

        if target_path.exists() and not PLUGIN_SETTINGS["FORCE_SAVE"]:
            logger.debug(f"Refusing to overwrite existing {target_path}")
            return

        article_title = self._get_article_title(content_object)

        img = self._generate_card_image(article_title)
        img.save(target_path)
