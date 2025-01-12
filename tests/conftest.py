"""Mocks Pelican objects required for the units tests."""

import textwrap

from PIL import Image
import pytest

from pelican.plugins.social_cards.cards_generator import CardsGenerator
from pelican.plugins.social_cards.settings import PLUGIN_SETTINGS


class FakeArticle:
    """Mock Pelican Article object."""

    def __init__(self, settings, metadata, title, url):
        self.settings = settings
        self.metadata = metadata
        self.title = title
        self.url = url

    def set_custom_data(self, data):
        """Set arbitrary data of the object."""
        for key, value in data.items():
            setattr(self, key, value)


@pytest.fixture()
def article():
    """Create a fake article."""
    settings = {
        "SITEURL": "https://www.fakesite.invalid",
    }
    title = "Fake Title"
    url = "fake-title.html"
    metadata = {
        "title": title,
        "url": url,
    }

    return FakeArticle(
        settings=settings,
        metadata=metadata,
        title=title,
        url=url,
    )


@pytest.fixture()
def default_settings():
    PLUGIN_SETTINGS.clear()

    PLUGIN_SETTINGS.update(
        **{
            "FONT_FILENAME": "tests/fonts/LiberationMono-Regular.ttf",
            "FONT_SIZE": 20,
            "FONT_FILL": "#000000",
            "FONT_OUTLINE_SIZE": 0,
            "FONT_OUTLINE_FILL": "#000000",
            "CANVAS_WIDTH": 300,
            "CANVAS_HEIGHT": 300,
            "CANVAS_LEFT": 0,
            "CANVAS_TOP": 0,
            "HORIZONTAL_ALIGNMENT": "left",
            "VERTICAL_ALIGNMENT": "top",
            "LEADING": 10,
            "KEY_NAME": "og_image",
            "WRAPPING_FUNCTION": textwrap.wrap,
            "CHARS_PER_LINE": 100,
        }
    )


@pytest.fixture()
def cards_generator():
    CardsGenerator._template = Image.new("RGB", (300, 300), "#ffffff")
    cd = CardsGenerator()
    return cd
